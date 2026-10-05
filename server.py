import threading
import socket
import protocol as proto

HOST = "0.0.0.0"
PORT = 5555

tasks_lock = threading.Lock()

LIST_TASKS = []


def handle_client(sock, addr):
    print(f"{addr} подключился")
    try:
        while True:
            try:
                msg = proto.recv_message(sock)
            except (ConnectionResetError, OSError):
                msg = None
            if msg is None:
                print(f"[!] {addr} - соединение закрыто")
                break

            command, payload = msg

            if command == "ADD":
                text = payload.decode()
                if not text.strip():
                    err = "Пустая задача"
                    proto.send_messages(sock, "UNKN", err.encode())
                else:
                    with tasks_lock:
                        LIST_TASKS.append((text, "[ ]"))
            elif command == "LIST":
                with tasks_lock:
                    list_copy = LIST_TASKS.copy()
                proto.send_messages(sock, "LIST")
                for i in list_copy:
                    for j in i:
                        proto.send_messages(sock, "TEXT", j.encode())
                proto.send_messages(sock, "STOP")
            elif command == "DONE":
                try:
                    number = int(payload.decode())
                    with tasks_lock:
                        LIST_TASKS[number - 1] = (LIST_TASKS[number-1][0],"[x]")
                except (ValueError, IndexError):
                    proto.send_messages(sock, "UNKN", "По такому номеру нет задачи".encode())
            elif command == "QUIT":
                print(f"[-] {addr} вышел через QUIT")
                break
            else:
                proto.send_messages(sock, "UNKN", "Неизвестная команда".encode())
    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        print(f"[!] {addr} - ошибка соединения: {e}")
    finally:
        try:
            sock.close()
        except OSError:
            pass
        print(f"{addr} отключён")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        print(f'Сервер слушает {HOST}:{PORT}')
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Сервер остановлен")