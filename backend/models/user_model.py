# backend/models/user_model.py

from datetime import datetime
from bson import ObjectId, Binary
import numpy as np


class UserModel:
    """MongoDB data-access layer for registered users.

    Iris codes and noise masks are packed into compact bytes (numpy.packbits)
    before storage so they stay well under MongoDB's 16 MB BSON limit.
    On read they are unpacked back to lists of 0s and 1s.
    """

    def __init__(self, db):
        self.collection = db["users"]

    # -----------------------------------------
    # Bit-packing helpers
    # -----------------------------------------
    @staticmethod
    def _pack_bits(bit_list):
        """Pack a list of 0/1 ints into BSON Binary bytes."""
        if bit_list is None:
            return None
        arr = np.array(bit_list, dtype=np.uint8)
        packed = np.packbits(arr)
        # Store the original length so we can unpack exactly
        length_bytes = len(bit_list).to_bytes(4, "big")
        return Binary(length_bytes + packed.tobytes())

    @staticmethod
    def _unpack_bits(binary_data):
        """Unpack BSON Binary bytes back to a list of 0/1 ints."""
        if binary_data is None:
            return None
        raw = bytes(binary_data)
        original_length = int.from_bytes(raw[:4], "big")
        packed = np.frombuffer(raw[4:], dtype=np.uint8)
        unpacked = np.unpackbits(packed)[:original_length]
        return unpacked.tolist()

    # -----------------------------------------
    # Create New User
    # -----------------------------------------
    def create_user(self, name, address, phone_no, relationship, iris_code, noise_mask=None):
        """Insert a new user document with their packed binary iris code."""
        user_data = {
            "name": name,
            "address": address,
            "phone_no": phone_no,
            "relationship": relationship,
            "iris_code": self._pack_bits(iris_code),
            "noise_mask": self._pack_bits(noise_mask),
            "created_at": datetime.utcnow(),
        }

        result = self.collection.insert_one(user_data)
        return str(result.inserted_id)

    # -----------------------------------------
    # Format Output Response
    # -----------------------------------------
    def format_user_response(self, user):
        return {
            "id": str(user.get("_id")),
            "name": user.get("name"),
            "address": user.get("address"),
            "phone_no": user.get("phone_no"),
            "relationship": user.get("relationship"),
            "registered_at": str(user.get("created_at", "")),
        }

    # -----------------------------------------
    # Get User By ID
    # -----------------------------------------
    def get_user_by_id(self, user_id):
        user = self.collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return self.format_user_response(user)
        return None

    # -----------------------------------------
    # Get All Iris Codes (For Matching)
    # -----------------------------------------
    def get_all_iris_codes(self):
        """Return all users with their iris codes and noise masks unpacked."""
        users = list(self.collection.find({}, {
            "name": 1,
            "address": 1,
            "phone_no": 1,
            "relationship": 1,
            "iris_code": 1,
            "noise_mask": 1,
        }))
        # Unpack binary data back to lists
        for user in users:
            user["iris_code"] = self._unpack_bits(user.get("iris_code"))
            user["noise_mask"] = self._unpack_bits(user.get("noise_mask"))
        return users

    # -----------------------------------------
    # Get All Users (Admin)
    # -----------------------------------------
    def get_all_users(self):
        """Return all users without iris codes (for admin listing)."""
        users = list(self.collection.find({}, {
            "name": 1,
            "address": 1,
            "phone_no": 1,
            "relationship": 1,
            "created_at": 1,
        }))
        return users

    # -----------------------------------------
    # Delete User By ID
    # -----------------------------------------
    def delete_user(self, user_id):
        result = self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    # -----------------------------------------
    # Count Users
    # -----------------------------------------
    def count_users(self):
        return self.collection.count_documents({})