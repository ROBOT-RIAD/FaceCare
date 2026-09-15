import cloudinary.uploader


def upload_image_to_cloudinary(image_file):
    result = cloudinary.uploader.upload(
        image_file,
        resource_type="image",
        folder="videostore/images",
    )

    return {
        "url": result.get("secure_url"),
        "public_id": result.get("public_id"),
    }