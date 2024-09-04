from app import app

if __name__ == '__main__':
    print(f"App config before run: {app.config}")  # Debug print
    app.run(debug=True)