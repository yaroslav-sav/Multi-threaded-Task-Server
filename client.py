import threading
import socket
import protocol as proto

HOST = "127.0.0.1"
PORT = 5555

input_active = threading.Event()
input_active.set()

def listen_loop(sock, stop_event):
    while not stop_event.is_set():
        try:
            msg = proto.recv_message(sock)
        except (ConnectionResetError, OSError):
            msg = None
        if msg is None:
            print("Соединение с сервером потеряно")
            stop_event.set()
            break
        command, payload = msg
        text = payload.decode()
        if command == "UNKN":
            print(text)
            input_active.set()
        elif command == "LIST":
            current_list = []
            while True:
                try:
                    msg = proto.recv_message(sock)
                except (ConnectionResetError, OSError):
                    print("Проблемы с соединением")
                    stop_event.set()
                    return
                if msg is None:
                    print("Соединение потеряно")
                    stop_event.set()
                    return
                command, payload = msg
                if command == "STOP":
                    break
                text = payload.decode()
                current_list.append(text)

            print("-" * 20)
            for i in range(0, len(current_list), 2):
                text = current_list[i]
                status = current_list[i + 1]
                print(f"{i // 2 + 1}. {status} {text}")
            print("-" * 20)
            input_active.set()



def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except (ConnectionRefusedError, OSError) as e:
        print(f"Не удалось подключиться: {e}")
        return

    stop_event = threading.Event()
    threading.Thread(target=listen_loop, args=(sock, stop_event), daemon=True).start()

    print("Команды:")
    print("/add <Ваша задача> - добавляет вашу задачу в список дел")
    print("/list - позволит вам увидеть список всех задач")
    print("/done <Номер задачи> - отметит задачу из списка как выполненную")
    print("/quit - выход из программы")

    try:
        while True:
            input_active.wait()
            line = input("> ")
            if line == "/quit":
                proto.send_messages(sock, "QUIT")
                break
            elif line.startswith("/add "):
                text = line[len("/add "):]
                if text.strip():
                    proto.send_messages(sock, "ADD", text.encode())
                else:
                    print("Нельзя добавить задачу как пустую строку")
            elif line == "/list":
                input_active.clear()
                proto.send_messages(sock, "LIST")
            elif line.startswith("/done "):
                number = line[len("/done "):]
                proto.send_messages(sock, "DONE", number.encode())
            else:
                print("Неизвестная команда")
    except (EOFError, KeyboardInterrupt, BrokenPipeError, OSError):
        pass
    finally:
        sock.close()


if __name__ == "__main__":
    main()