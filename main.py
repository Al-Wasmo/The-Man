import utils
from model import *
from workspace import *


utils.init()

# model = Model()
# model.do("how are you today")


workspace = WorkSpace()
posts = workspace.get_feed_posts(offset=10)
print(posts)
# workspace.react_to_post("7347934728584388608")