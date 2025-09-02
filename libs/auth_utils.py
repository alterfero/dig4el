from streamlit_authenticator.utilities.hasher import Hasher

def make_hash(plain_password):
    h = Hasher.hash(plain_password)
    return h

print(make_hash("jacques.vernaudon@gmail.com"))

