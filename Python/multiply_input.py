# multiply_input_loop.py

FACTOR = 3.391685

while True:
    user_input = input("Enter a number, or type q to quit: ")

    if user_input.lower() in ("q", "quit", "exit"):
        break

    try:
        number = float(user_input)
        result = number * FACTOR
        print(result)
    except ValueError:
        print("Error: please enter a valid number.")