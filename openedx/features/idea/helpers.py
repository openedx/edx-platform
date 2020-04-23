def upload_to_path(instance, filename, folder):
    """
    Create and return path where files will be uploaded. This path has specific formation
    i.e. app_label/folder/filename
    :param instance: An instance of the model where the FileField is defined
    :param filename: The filename that was originally given to the file
    :param folder: The specific folder where files will be uploaded
    :return: path to upload files
    """
    return '{app_label}/{folder}/{filename}'.format(
        app_label=instance._meta.app_label,
        filename=filename,
        folder=folder
    )
