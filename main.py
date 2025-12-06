"""
7K Guild OCR Manager Tool
Developed By: SusiShushii
GitHub: https://github.com/SusiShushii/7K-Guild-OCR-Tool
Description:
    OCR automation tool for Boss Guild, Castle, and Growth reports.

NOTE:
    This header is for documentation only.
    It does NOT print when the program runs.
"""

import warnings
warnings.filterwarnings("ignore",message=".*pin_memory.*",category=UserWarning)

from app import (
    process_boss_guild,
    process_castle,
    run_boss_growth,
    run_castle_growth,
)

def run_option(opt):
    """Run the function that corresponds to the selected menu number."""
    if opt == 1:
        print("\n🚀 Running Boss Guild OCR...\n")
        process_boss_guild()
    elif opt == 2:
        print("\n🚀 Running Castle OCR...\n")
        process_castle()
    elif opt == 3:
        print("\n📈 Running Boss Guild Growth Report...\n")
        run_boss_growth()
    elif opt == 4:
        print("\n📈 Running Castle Growth Report...\n")
        run_castle_growth()


def parse_choice(text: str):
    """
    Parse user input such as:
        1-4   → [1, 2, 3, 4]
        1-3   → [1, 2, 3]
        1,3,4 → [1, 3, 4]
        3     → [3]

    (Does not support concatenated input like 134)
    """
    text = text.replace(" ", "")

    # กรณีช่วง 1-4
    if "-" in text:
        parts = text.split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            start = int(parts[0])
            end = int(parts[1])
            return list(range(start, end + 1))

    # กรณีคั่นด้วย comma เช่น 1,3,4
    if "," in text:
        nums = [x for x in text.split(",") if x.isdigit()]
        return list(dict.fromkeys(int(x) for x in nums))

    # กรณีเลขตัวเดียว เช่น "3"
    if text.isdigit() and len(text) == 1:
        return [int(text)]

    return []

def main_menu():
    while True:
        print("\n============================================")
        print("        🔥 Guild OCR Tool – Main Menu 🔥")
        print("============================================")
        print("1) Boss Guild OCR")
        print("2) Castle OCR")
        print("3) Boss Guild Growth Report")
        print("4) Castle Growth Report")
        print("0) Exit")
        print("============================================")

        user_input = input("Enter your choice examples: (1-4) , (1,3,4) , (2): ").strip()
        if user_input == "0":
            print("\n👋 Bye!")
            break

        options = parse_choice(user_input)

        if not options:
            print("\n❌ รูปแบบไม่ถูกต้อง ลองใหม่...")
            continue

        # รันตามลำดับ และกันซ้ำ
        ran = set()
        for opt in options:
            if opt in {1, 2, 3, 4} and opt not in ran:
                run_option(opt)
                ran.add(opt)

        input("\n✅ เสร็จแล้ว! กด Enter เพื่อกลับเมนู...")


if __name__ == "__main__":
    main_menu()
