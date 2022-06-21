import sys

if __name__ == "__main__":
    print(f"Arguments count: {len(sys.argv)}")
    for i in sys.argv:
        print(f'Argument: {i:>10}')