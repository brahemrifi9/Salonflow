import random
import string

def generate_booking_ref():
    chars = string.ascii_uppercase + string.digits
    code = "".join(random.choices(chars, k=5))
    return f"SF-{code}"