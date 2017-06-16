"""gpg2 interface"""

import subprocess


class GPG:
    """Interface to gpg2"""

    bin = "gpg2"

    def __init__(self):
        pass

    class DecryptionException(Exception):
        """Exception while decrypting."""
        pass

    class EncryptionException(Exception):
        """Exception while encrypting."""
        pass

    def from_file(self, file):
        """Decrypt file located at filepath."""
        must_close = False
        if isinstance(file, str):
            try:
                file = open(file, "rb")
            except (FileNotFoundError, PermissionError) as e:
                raise GPG.DecryptionException(str(e))
            else:
                must_close = True
        result = subprocess.run(
            [GPG.bin, "--decrypt"],
            input=file.read(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if must_close:
            file.close()
        if result.returncode == 0:
            data = result.stdout
            return data
        else:
            raise GPG.DecryptionException(result.stderr)

    def to_file(self, data, file, pubkey_id):
        """
        Encrypt data and store it in file
        data must be bytes-like
        """
        must_close = False
        if isinstance(file, str):
            try:
                file = open(file, "wb")
            except PermissionError as e:
                raise GPG.EncryptionException(str(e))

        result = subprocess.run(
            [GPG.bin, "--encrypt", "-r", pubkey_id],
            input=data,
            stdout=file,
            stderr=subprocess.PIPE
        )
        if must_close:
            file.close()
        if result.returncode == 0:
            # It was successful
            return
        else:
            raise GPG.EncryptionException(result.stderr)



def test():
    """Test the module."""
    try:
        gpg = GPG()
        # Write data to a file, read it back in, and check it
        data = "This is a test\nThis is a second line"
        filename = "gpgtestfile.txt.gpg"
        pubkey_id = "kevin@schmittle.net"

        try:
            gpg.to_file(bytes(data, encoding="utf-8"), filename, pubkey_id)
        except Exception as e:
            print("Encryption failed: {}".format(e))
            return

        try:
            contents = gpg.from_file(filename)
        except Exception as e:
            print("Decryption failed: {}".format(e))

        contents = str(contents, encoding="utf-8")
        if contents != data:
            print("Test failed: '{}' != '{}'".format(contents, data))
    except Exception:
        pass
    else:
        print("All tests passed")


if __name__ == "__main__":
    test()
