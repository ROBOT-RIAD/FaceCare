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




def delete_image_from_cloudinary(public_id):
    if not public_id:
        return False

    result = cloudinary.uploader.destroy(
        public_id,
        resource_type="image",
        invalidate=True,
    )

    return result.get("result") == "ok"