import constants as c

class Statistic:
    def __init__(self):
        self.player_wins = {}
        self.total_games = 0
        with open(c.FILE_PATH_WINS, 'r') as file:
            lines = file.readlines()
            for line in lines:
                player, wins = line.strip().split(':')
                self.player_wins[player] = int(wins)
                self.total_games += int(wins)

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
        """
        Get the number of wins for a specific player.

        Args:
            player_name (str): The name of the player.

        Returns:
            int: The number of wins for the player. If the player has no wins, 0 is returned.
        """
        return self.player_wins.get(player_name, 0)
    

    def get_answer_frequency(self, answer):
        return self.frequency_of_answers.get(answer, 0)

    def get_total_games(self):
        return self.total_games
    
    # get the player with the most wins
    def get_leader(self):
        if len(self.player_wins) == 0:
            return None
        return max(self.player_wins, key=self.player_wins.get)
    
    
    # function that print each player and their wins sorted by wins
    def print_player_wins(self):
        print("Player Wins")
        for player in sorted(self.player_wins, key=self.player_wins.get, reverse=True):
            print(f"{player}: {self.player_wins[player]}")

    # update the player_wins file
    def update_file(self):
        with open(c.FILE_PATH_WINS, 'w') as file:
            for player, score in self.player_wins.items():
                file.write(f"{player}:{score}\n")


