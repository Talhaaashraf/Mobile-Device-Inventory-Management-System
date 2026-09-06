import bcrypt

password = "Admin123!"
hash_from_db = "$2b$12$e4jHiXymgqa2EpuxmBvLquB52J2BGuiIlzelPf4uF3BbhBCqKffCW"

result = bcrypt.checkpw(password.encode(), hash_from_db.encode())
print("Password matches:", result)