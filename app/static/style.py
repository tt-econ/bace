css_style = """
:root {
    --background-color: #04362c;
    --box-color: #b4c3c0;
    --option-color: #b4c3c0;
    --hover-color: #829b96;
    --alt-color: #688680;
}

body {
    background-color: var(--background-color);
    font-family: Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    margin: 0;
}

.question-box {
    background-color: var(--box-color);
    padding: 20px 20px 60px 20px;
    width: 80%;
    min-width: 850px;
    position: relative;
}

.question-text {
    text-align: center;
    margin-bottom: 28px;
}

.options {
    display: flex;
    flex-direction: row;
    justify-content: center;
    align-items: center;
    width: 90%;
    margin-left: auto;
    margin-right: auto;
}

.radio-container {
    display: block;
    position: relative;
    cursor: pointer;
    user-select: none;
    width: auto;
    text-align: center;
    margin: 0 10px;
}

.radio-container input {
    position: absolute;
    opacity: 0;
    cursor: pointer;
    height: 0;
    width: 0;
}

.radio-checkmark {
    display: inline-block;
    padding: 5px 15px;
    background-color: var(--option-color);
    border-radius: 4px;
    width: 100%;
    box-sizing: border-box;
}

.radio-container:hover .radio-checkmark {
    background-color: var(--hover-color);
}

.radio-container input:checked~.radio-checkmark {
    background-color: var(--alt-color);
}

#next-button {
    position: absolute;
    right: 20px;
    display: none;
    background-color: var(--alt-color);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    margin-top: 0px;
    align-self: flex-end;
}
"""
