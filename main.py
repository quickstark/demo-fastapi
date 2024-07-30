from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from src.amazon import *
from src.mongo import *
from src.openai import *
from src.postgres import *

# Setup CORS
origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://quickstark-vite-images.up.railway.app/",
]

# Instantiate the FastAPI app
app = FastAPI(debug=True)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

# Include the routers
app.include_router(router_openai)
app.include_router(router_amazon)
app.include_router(router_mongo)
app.include_router(router_postgres)

# Define Python user-defined exceptions

class CustomError(Exception):
    """Base class for custom  exceptions"""

    def __init__(self, message):
        self.message = message


@app.get("/images")
async def get_all_images(backend: str = "mongo"):
    print(f"Getting all images from {backend}")
    if backend == "mongo":
        images = await get_all_images_mongo()
    elif backend == "postgres":
        images = await get_all_images_postgres()
    else:
        raise CustomError("Invalid backend specified")
    return images


@app.post("/add_image", status_code=201)
async def add_photo(file: UploadFile, backend: str = "mongo"):
    print(f"Uploading File ${file.filename} - ${file.content_type}")

    # Attempt to upload the image to Amazon S3
    try:
        s3_url = amazon_upload(file)
        # check if the file url is null
        if s3_url is None:
            raise CustomError("Error uploading image to Amazon S3")
    except CustomError as err:
        capture_exception(err)

    # Attempt to detect labels and text in the image using Amazon Rekognition
    try:
        # amazon_detection(file) returns a tuple of 3 lists
        amzlabels, amztext, amzmoderation = amazon_detection(file)
        if not amzlabels and not amztext and not amzmoderation:
            raise CustomError("Error processing Amazon Rekognition")
    except CustomError as err:
        capture_exception(err)

    # Check the image for questionable content using Amazon Rekognition
    try:
        if amazon_moderation(amzmoderation):
            return {"message": f"{file.filename} may contain questionable content. Let's keep it family friendly. ;-)"}
            raise CustomError("We detected inappropriate content")
    except CustomError as err:
        capture_exception(err)

    # Check if the image contained the word "error" and issue an error
    try:
        if amazon_error_text(amztext):
            error_message = f"Image Text Error - {' '.join(amztext)}"
            raise CustomError(error_message)
    except CustomError as err:
        capture_exception(err)

    # Check if the image labels contained the word "bug" or "insect" and issue an error
    try:
        if amazon_error_label(amzlabels):
            error_message = f"Image Label Error - {' '.join(amzlabels)}"
            raise CustomError(error_message)
    except CustomError as err:
        capture_exception(err)

    if backend == "mongo":
        # Attempt to upload the image to MongoDB
        print("Adding image to MongoDB")
        try:
            await add_image_mongo(file.filename, s3_url, amzlabels, amztext)
        except CustomError as err:
            capture_exception(err)
    elif backend == "postgres":
        # Attempt to upload the image to Postgres
        try:
            await add_image_postgres(file.filename, s3_url, amzlabels, amztext)
        except CustomError as err:
            capture_exception(err)
    else:
        raise CustomError("Backend not supported")


@app.delete("/delete_image/{id}", status_code=201)
async def delete_image(id, backend: str = "mongo"):
    print(f"Attempt to Delete File {id} from {backend}")

    if backend == "mongo":
        # Attempt to delete the image from MongoDB
        try:
            image = await get_one_mongo(id)
            res = await delete_one_mongo(id)
        except CustomError as err:
            capture_exception(err)
    elif backend == "postgres":
        # Attempt to delete the image from Postgres
        try:
            image = await get_image_postgres(id)
            res = await delete_image_postgres(id)
        except CustomError as err:
            capture_exception(err)
    else:
        raise CustomError("Backend not supported")

    # Attempt to delete the image from Amazon S3
    try:
        print(image)
        res = await amazon_delete_one_s3(image["name"])
        print(res)
    except CustomError as err:
        capture_exception(err)


@app.get("/")
async def root():
    return {"message": "API Root. Welcome to FastAPI!"}
