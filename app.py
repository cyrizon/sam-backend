from src import config
from src import app

if __name__ == "__main__":
    app.run(host= config.HOST,
            port= config.PORT,
            debug= config.DEBUG)