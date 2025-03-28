import curses

def choose_language(stdscr):
    curses.curs_set(0)  # Hide cursor
    stdscr.clear()
    
    options = ["Telugu", "English"]
    current_index = 0

    while True:
        stdscr.clear()

        stdscr.addstr(1, 4, "🌟 Choose your preferred language 🌟", curses.A_BOLD)

        for i, option in enumerate(options):
            if i == current_index:
                stdscr.attron(curses.color_pair(1))  # Highlight selected option
                stdscr.addstr(3 + i, 6, f"> {option} <")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(3 + i, 6, f"  {option}")

        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP and current_index > 0:
            current_index -= 1
        elif key == curses.KEY_DOWN and current_index < len(options) - 1:
            current_index += 1
        elif key in [10, 13]:  # Enter key pressed
            return "telugu" if current_index == 0 else "english"

def main():
    curses.wrapper(lambda stdscr: setup_curses(stdscr))

def setup_curses(stdscr):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # Highlight color

    language = choose_language(stdscr)
    print(f"\n✅ Starting conversation in **{language.capitalize()}** mode... 🎙️")

if __name__ == "__main__":
    main()



