from datetime import date
DEFAULT_DATE_FORMAT = '%B %d, %Y'
LOCALE = 'en_US.UTF-8'  
# Basic settings
AUTHOR = 'HengyeZhu'
SITENAME = 'Hengye_Blog'
SITEURL = "https://hengyezhu.github.io"
PATH = "content"
TIMEZONE = 'Asia/Shanghai'
DEFAULT_LANG = 'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Social widget
SOCIAL = (
    ("github", "https://github.com/HengyeZhu"),      
)

# Pagination
DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True

# Theme settings
THEME = 'theme/minimal-xy'

# Theme customizations
MINIMALXY_START_YEAR = 2025
MINIMALXY_CURRENT_YEAR = date.today().year

# Author settings
AUTHOR_INTRO = 'Hi! I am Hengye Zhu - an undergraduate student at Shanghai Jiao Tong University. I am interested in NeuroAI.'
AUTHOR_DESCRIPTION = 'Hengye Zhu is an undergraduate student at Shanghai Jiao Tong University. He is interested in NeuroAI, Applied Mathematics and Control Theory. His research experience includes developing computational neuronal models and brain-inspired algorithms. In his free time, Hengye enjoys playing badminton and writing tech blogs.' 
AUTHOR_AVATAR = 'https://avatars.githubusercontent.com/u/186930454?s=400&u=0bc1b19dad19038c8d03179fd57ac30cf4b71f15&v=4'
AUTHOR_WEB = 'https://github.com/HengyeZhu'


