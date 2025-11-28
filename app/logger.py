import logging

logging.basicConfig(
    filename="quiz_solver.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log(msg: str):
    logging.info(msg)
    print(msg)  # also show in console
