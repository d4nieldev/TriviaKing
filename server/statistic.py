class Statistic:
    def __init__(self):
        self.player_wins = {}
        self.frequency_of_answers = {}
        self.total_games = 0

    def add_player_win(self, player_name):
        if player_name in self.player_wins:
            self.player_wins[player_name] += 1
        else:
            self.player_wins[player_name] = 1

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
    
    def get_leader_wins(self):
        leader = self.get_leader()
        if leader is None:
            return 0
        return self.player_wins[leader]