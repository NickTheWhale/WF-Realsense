from app import App


def main():
    app = App("ROI Utility")

    # gui loop
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
