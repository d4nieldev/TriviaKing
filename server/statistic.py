import json
import constants as c

class Statistic:
    def __init__(self):
        self.player_wins = {}
        self.total_games = 0
        try:
            with open(c.FILE_PATH_WINS, 'r') as file:
                self.player_wins = json.load(file)
                self.total_games = sum(self.player_wins.values())
        except FileNotFoundError:
            self.player_wins = {}
            self.total_games = 0

        self.frequency_of_answers = {}

    def add_player_win(self, player_name):
        self.increment_total_games()
        if player_name in self.player_wins:
            self.player_wins[player_name] += 1
        else:
            self.player_wins[player_name] = 1
        
        self.update_file()

    def add_answer_frequency(self, answer):
        if answer in self.frequency_of_answers:
            self.frequency_of_answers[answer] += 1
        else:
            self.frequency_of_answers[answer] = 1

    def increment_total_games(self):
        self.total_games += 1

    def get_player_wins(self, player_name : str):
        return self.player_wins.get(player_name, 0)

    def get_answer_frequency(self, answer):
        return self.frequency_of_answers.get(answer, 0)

    def get_total_games(self):
        return self.total_games

    def get_leader(self):
        if not self.player_wins:
            return None
        return max(self.player_wins, key=self.player_wins.get)
    
    def print_player_wins(self):
        sorted_players = sorted(self.player_wins.items(), key=lambda x: x[1], reverse=True)
        # Ensure there are three players (fill with "Empty" if fewer than three)
        while len(sorted_players) < 3:
            sorted_players.append(("-", 0))
            
        top_3 = [f"{player}" for player, _ in sorted_players[:3]]
        
        full_res = '\n'.join([f"{player}: {wins}" for player, wins in sorted_players])
        print(c.PODIUM_STR.format(top_3[0], top_3[1], top_3[2], full_res))


    def update_file(self):
        with open(c.FILE_PATH_WINS, 'w') as file:
            json.dump(self.player_wins, file, indent=4)
            