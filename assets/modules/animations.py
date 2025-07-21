import os
from time import sleep as sl


# Animation function to show progress
def anim(text, tx, t):
    """
    Display an animated progress bar.

    Parameters:
    text (str): Text to display before the animation.
    tx (str): Text to display after the animation completes.
    t (int): Duration of the animation in seconds.
    """
    for _ in range(t):
        for frame in "-\\|/":
            print(f"\r{text} {frame}", end="", flush=True)
            sl(0.1)
    print(f"\r{text} {tx}")


# Animation function to show database access progress
def access_anim(tx, t):
    """
    Display an animation indicating database access.

    Parameters:
    tx (str): Text to display after the animation completes.
    t (int): Duration of the animation in seconds.
    """
    for p in range(t):
        print("\rAccessing Database <<[" + "!" * p + "]>>", end="", flush=True)
        sl(0.001)
    print("\rAccessing Database <<[" + tx + "]>>")


if __name__ == '__main__':
    print("This file includes necessary animation functions of the terminal, it will not do what you want this way...")
    input("Press enter to terminate...")
