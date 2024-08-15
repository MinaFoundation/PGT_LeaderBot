import hashlib


def hasher(arg1, arg2, arg3):
    combined_string = str(arg1) + str(arg2) + str(arg3)
    sha256_hash = hashlib.sha256()
    sha256_hash.update(combined_string.encode("utf-8"))
    hash_hex = sha256_hash.hexdigest()

    return hash_hex
