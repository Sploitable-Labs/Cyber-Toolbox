import configparser
import praw
import networkx as nx
import matplotlib.pyplot as plt
import json
import pandas as pd

class RedditInterface:
    reddit = None
    reddit_username = ""
    reddit_password = ""
    reddit_client_id = ""
    reddit_client_secret = ""
    reddit_user_agent = ""
    reddit_subreddit_name = ""

    def __init__(self, config="osint.ini"):
        self.load_config(config)

        self.reddit = praw.Reddit(
            client_id=self.reddit_client_id,
            client_secret=self.reddit_client_secret,
            password=self.reddit_password,
            user_agent=self.reddit_user_agent,
            username=self.reddit_username
        )

    def load_config(self, config):
        conf = configparser.ConfigParser()
        conf.read(config)
        self.reddit_username = conf['reddit']['username']
        self.reddit_password = conf['reddit']['password']
        self.reddit_client_id = conf['reddit']['client_id']
        self.reddit_client_secret = conf['reddit']['client_secret']
        self.reddit_user_agent = conf['reddit']['user_agent']

    def get_commenters(self, subreddit_name):
        subscribers = set()
        subreddit = self.reddit.subreddit(subreddit_name)
        for comment in subreddit.comments(limit=1000):
            if comment.author:
                subscriber = comment.author.name
                subscribers.add(subscriber)
        return list(subscribers)


def add_commenters_to_graph(graph, subreddit_name, subscribers):
    graph.add_node(subreddit_name)
    for subscriber in subscribers:
        graph.add_node(subscriber)
        graph.add_edge(subscriber, subreddit_name)


def main():
    rif = RedditInterface()
    graph = nx.Graph()

    config_path = "commenters.ini"

    conf = configparser.ConfigParser()
    conf.read(config_path)

    commenters = {}
    subreddits = [
        'AskNetSec',
        'Blackhat',
        'blueteamsec',
        'ComputerSecurity',
        'crypto',
        'Cybersecurity',
        'hacking',
        'HowToHack',
        'Infosec',
        'InfoSecNews',
        'Malware',
        'MalwareAnalysis',
        'netsec',
        'netsecstudents',
        'onions',
        'opsec',
        'OSINT',
        'Passwords',
        'privacy',
        'ReverseEngineering',
        'security',
        'TOR',
        'WindowsSecurity'
    ]

    # Build graph layout
    for subreddit in subreddits:

        if subreddit in conf.sections():
            print("Loading '{}' commenters from config".format(subreddit))
            commenters[subreddit] = json.loads(conf.get(subreddit, "commenters"))

        else:
            sub_commenters = rif.get_commenters(subreddit)
            commenters[subreddit] = sub_commenters
            print("Adding '{}' commenters to the config".format(subreddit))
            conf.add_section(subreddit)
            conf.set(subreddit, "commenters", json.dumps(sub_commenters))

        count = len(commenters[subreddit])
        print("Adding {} subscribers from '{}' to the graph".format(count, subreddit))
        add_commenters_to_graph(graph, subreddit, commenters[subreddit])

    print("Updating config file")
    with open(config_path, 'w') as configfile:
        conf.write(configfile)

    print("Finding nodes with only a single connection")
    nodes_to_remove = [node for node, degree in dict(graph.degree()).items() if degree < 5]

    print("Removing {} of {} nodes from the graph".format(len(nodes_to_remove), len(graph.nodes)))
    graph.remove_nodes_from(nodes_to_remove)

    print("Calculating graph layout")
    df = pd.DataFrame(index=graph.nodes(), columns=graph.nodes())
    for row, data in nx.shortest_path_length(graph):
        for col, dist in data.items():
            df.loc[row, col] = dist
    df = df.fillna(df.max().max())
    layout = nx.kamada_kawai_layout(graph, dist=df.to_dict())

    print("Plotting graph")
    nodes = graph.nodes()

    plt.figure()
    plt.axis('off')
    for subreddit in subreddits:
        print("Plotting nodes from '{}".format(subreddit))
        nx.draw_networkx(graph, pos=layout, nodelist=[subreddit], node_size=4000, node_color='#FFFF00', font_size=10, width=3)
        for sub_commenters in nodes:
            if sub_commenters not in subreddits:
                nx.draw_networkx(graph, pos=layout, nodelist=[sub_commenters], node_size=3000, node_color='#A0CBE2', font_size=8, width=3)

    [print(node, degree) for node, degree in dict(graph.degree()).items() if node not in subreddits]

    print("Rendering graph")
    plt.show()



if __name__ == "__main__":
    main()
