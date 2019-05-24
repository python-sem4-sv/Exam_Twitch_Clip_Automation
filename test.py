test_var = "This hasnt been changed yet"



def main():
    global test_var
    test_var = "This has been changed"

if __name__ == "__main__":
    main()
    print(test_var)

    