import utils
c = utils.get_config()
for param in c['MySQL']:
    print(param, ':', c['MySQL'][param])