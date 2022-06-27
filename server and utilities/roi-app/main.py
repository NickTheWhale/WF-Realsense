from app import App


def main():
    try:
        app = App("ROI Utility")
    except RuntimeError as e:
        print(e)
    else:
        # gui loop
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()


if __name__ == "__main__":
    main()
