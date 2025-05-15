from cryptography.fernet import Fernet
import json

# Hardcoded encryption key
HARD_CODED_KEY = b'L2dMjBcfWxzcRI8E4SyT4dQdEzqFzEbgLNEUPPX6HVo=' 

# Encrypt the JSON file
def encrypt_userdata():
    f = Fernet(HARD_CODED_KEY)
    with open("admindata.json", "rb") as file:
        data = file.read()

    encrypted_data = f.encrypt(data)
    with open("admindata.json", "wb") as file:
        file.write(encrypted_data)

def encrypt_settings():
    f = Fernet(HARD_CODED_KEY)

    with open("settings.json", "rb") as file_settings:
        data_setting = file_settings.read()

    encrypted_data_settings = f.encrypt(data_setting)
    with open("settings.json", "wb") as file_settings:
        file_settings.write(encrypted_data_settings)

# Decrypt the JSON file
def decrypt_file():
    f = Fernet(HARD_CODED_KEY)

    with open("admindata.json", "rb") as file:
        encrypted_data = file.read()

    with open("settings.json", "rb") as file_settings:
        encrypted_data_setting = file_settings.read()

    decrypted_data = f.decrypt(encrypted_data)
    decrypted_data_settings = f.decrypt(encrypted_data_setting)

    return [json.loads(decrypted_data), json.loads(decrypted_data_settings)]

# Replace the entire settings data
def replace_set(new_data):
    # Directly write the new data to settings.json
    with open("settings.json", "w") as file:
        json.dump(new_data, file)

    encrypt_settings()  # Re-encrypt the settings

# Replace the entire password data
def replace_password(new_data):
    # Directly write the new data to admindata.json
    with open("admindata.json", "w") as file:
        json.dump(new_data, file)

    encrypt_userdata() 


# if __name__ == "__main__":
#     # Encrypt the files initially (do this only once)
#encrypt_settings()
#     #encrypt_userdata()

#     # Replace the entire settings and password

#replace_password({"admin": "dilshan", "pass": "123"})

#     # Print the decrypted data to verify the changes
#print("Decrypted User Data:", decrypt_file()[0])
#print("Decrypted Settings Data:", decrypt_file()[1])
# replace_set(
# {
#     'storage_location': 'C:/Users/ashen/OneDrive/Desktop/pictures',
#     'nps': {
#         "no_of_rois": 40,
#         "roi_size": "(64, 64)",
#         "dist_c_to_record": 150,
#         "record_size": 0,
#         "f_rebin_increment": 1,
#         "run_avg_stack": True,
#         "min_slice": 1,
#         "max_slice": 40
#         },

#     'mtf': {
#         "obj_diameter": "25",
#         "circle_1":[[222, 231], [160, 190]],
#         "circle_2":[[166, 177], [205, 235]],
#         "circle_3":[[149, 159], [289, 319]],
#         "circle_4":[[193, 203], [373, 403]],
#         "circle_5":[[285, 295], [395, 425]],
#         "obj_diameter": 25,
#         "pixel_red_factor": 5,
#         "f_rebin_increment": 0.05,
#         "run_avg_stack": True,
#         "min_slice": 1,
#         "max_slice": 40
#     },
#     "mtf_3d": {
#         "pixel_spacing": 1,
#         "sigma": 2,
#         "pixel_reduction_factor": 1,
#         "rebin_factor": 1
#       },
#     "mean": {
#         "r1": 9,
#         "r2": 13,
#         "r3": 15,
#         "r4": 17,
#         "r5": 19,
#         "c1loc": (156, 224),
#         "c2loc": (195, 171),
#         "c3loc": (275, 151),
#         "c4loc": (353, 195),
#         "c5loc": (373, 288)
#       },
#     "uniformity": {
#         "min_slice": 1,
#         "max_slice": 40
#     }
# })


# "circle_1":[[], []] means y,x range