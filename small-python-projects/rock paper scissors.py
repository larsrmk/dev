import random

class ColoredText:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    WHITE = '\033[95m'
    ENDC = '\033[0m'

def player_choice():
    print("1. rock\n2. paper\n3. scissors")
    return input("Choose 1/2/3: ")

def computer_choice():
    return str(random.randint(1, 3))

def result(pc, cc, score):
    print(f"You selected {pc}.")
    print(f"The computer selected {cc}.")

    if pc == cc:
        print(ColoredText.YELLOW + "Draw!" + ColoredText.ENDC)
    elif (pc == "1" and cc == "3") or (pc == "2" and cc == "1") or (pc == "3" and cc == "2"):
        print(ColoredText.GREEN + "You win!" + ColoredText.ENDC)
        score += 1
    else:
        print(ColoredText.RED + "Computer wins!" + ColoredText.ENDC)
        print(f"Your final score: {score}")
        score = 0

    return score

if __name__ == "__main__":
    print("\nWelcome to rock, paper, scissors:")

    score = 0  # Initialisiere die score-Variable vor der Schleife

    while True:
        pc = player_choice()
        cc = computer_choice()

        score = result(pc, cc, score)

        repeat = input("\nOne more game (y/n)? ").lower()
        if repeat != "y":
            print("See ya!")
            break





