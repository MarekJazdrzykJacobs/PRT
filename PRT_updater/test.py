import datetime
from pathlib import Path

data = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
PATH_TO_FOLDER_FOR_DOWNLOAD = str(Path.home() / "Downloads")

with open(Path(PATH_TO_FOLDER_FOR_DOWNLOAD).joinpath('rower.txt'), "w") as f:
    f.write(f'{data}')