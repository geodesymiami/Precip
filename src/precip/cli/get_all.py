import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--name', type=str, help='Name of the location')

    inps = parser.parse_args()

    # Define the base command
    base_command = ["python3", "/Users/giacomo/code/precip/src/precip/cli/get_precipitation_lalo.py", "--name", inps.name, "--end-date", "20001201"]

    # Define the different styles
    styles = ["bar", "map", "annual"]

    # For each style, call the get_precipitation_lalo.py script with the appropriate arguments
    for style in styles:
        command = base_command + ["--style", style]
        result = subprocess.run(command, capture_output=True, text=True)

if __name__ == '__main__':
    main()