import streamlit as st
import random
import math
import time
from tabulate import tabulate
import os

# --- Project Class (Same as before) ---
class Project:
    def __init__(self, name, cost, life, annual_cash_flow, real_option, risk_level, user_gain):
        self.name = name
        self.cost = cost
        self.life = life
        self.annual_cash_flow = annual_cash_flow
        self.real_option = real_option
        self.risk_level = risk_level
        self.user_gain = user_gain
        self.owner = None
        self.purchase_round = None

    def calculate_npv(self, discount_rate=0.10):
        npv = -self.cost
        for year in range(1, self.life + 1):
            npv += self.annual_cash_flow / ((1 + discount_rate) ** year)
        return npv

    def calculate_irr(self):
        return (self.annual_cash_flow * self.life - self.cost) / (self.cost * self.life)

    def calculate_payback_period(self):
        return self.cost / self.annual_cash_flow

    def calculate_profitability_index(self, discount_rate=0.10):
        present_value = 0
        for year in range(1, self.life + 1):
            present_value += self.annual_cash_flow / ((1 + discount_rate) ** year)
        return present_value / self.cost

# --- FinancingOption Class (Same as before) ---
class FinancingOption:
    def __init__(self, name, description, max_amount, conditions, impact):
        self.name = name
        self.description = description
        self.max_amount = max_amount
        self.conditions = conditions
        self.impact = impact

# --- Event Class (Same as before) ---
class Event:
    def __init__(self, name, description, impact):
        self.name = name
        self.description = description
        self.impact = impact

# --- Tile Class (Same as before) ---
class Tile:
    def __init__(self, position, name, tile_type, action=None):
        self.position = position
        self.name = name
        self.tile_type = tile_type
        self.action = action

# --- Player Class (Same as before) ---
class Player:
    def __init__(self, name, starting_cash=100):
        self.name = name
        self.cash = starting_cash
        self.users = 1
        self.position = 0
        self.projects = []
        self.financing_history = []
        self.debt = 0
        self.equity_dilution = 0
        self.vc_funding_used = False
        self.ipo_done = False
        self.skip_next_turn = False

    def calculate_total_npv(self, current_round):
        total_npv = 0
        for project in self.projects:
            remaining_life = project.life - (current_round - project.purchase_round)
            if remaining_life > 0:
                npv = 0
                for year in range(1, remaining_life + 1):
                    npv += project.annual_cash_flow / ((1 + 0.10) ** year)
                total_npv += npv
        total_npv *= (1 - self.equity_dilution)
        if self.ipo_done:
            total_npv *= 0.7
        return total_npv

    def can_afford(self, amount):
        return self.cash >= amount

    def pay(self, amount):
        if self.can_afford(amount):
            self.cash -= amount
            return True
        return False

    def receive(self, amount):
        self.cash += amount

    def add_users(self, count):
        self.users += count

    def lose_users(self, count):
        self.users = max(0, self.users - count)

    def add_project(self, project, current_round):
        project.owner = self
        project.purchase_round = current_round
        self.projects.append(project)

    def add_financing(self, financing, amount):
        self.financing_history.append((financing, amount))
        if financing.name == "Debt":
            self.debt += amount
        elif financing.name == "VC Funding":
            self.vc_funding_used = True
            self.equity_dilution += 0.10
        elif financing.name == "Equity":
            self.equity_dilution += 0.20
        elif financing.name == "IPO":
            self.ipo_done = True

    def pay_debt_interest(self):
        interest = self.debt * 0.06
        if self.can_afford(interest):
            self.cash -= interest
            return True
        return False

    def collect_project_revenues(self):
        total_revenue = 0
        for project in self.projects:
            total_revenue += project.annual_cash_flow
        self.cash += total_revenue
        return total_revenue

# --- Finopoly Game Class ---
class Finopoly:
    def __init__(self):
        self.players = []
        self.current_round = 1
        self.current_player_index = 0
        self.board = []
        self.projects = []
        self.financing_options = []
        self.events = []
        self.game_over = False
        self.num_rounds = 5 # Set the number of rounds

        self.initialize_game()

    def initialize_game(self):
        self.create_projects()
        self.create_financing_options()
        self.create_events()
        self.create_board()

    def create_projects(self):
        self.projects = [
            Project("Expand to Asia Market", 50, 3, 20, "Expand", "High", 2),
            Project("Referral Program", 20, 3, 12, "Scale", "Low", 1.5),
            Project("Retail Partnership", 40, 3, 18, "User Trust", "High", 1.8),
            Project("AI Fraud Prevention", 30, 3, 15, "Efficiency Gain", "Medium", 1),
            Project("Product Launch", 35, 2, 25, "Rebrand", "Medium", 2.5),
            Project("Mobile App Redesign", 25, 2, 15, "User Experience", "Low", 1.2),
            Project("Blockchain Integration", 45, 3, 17, "Security", "High", 1.5),
            Project("Customer Support AI", 30, 2, 18, "Efficiency", "Medium", 0.8)
        ]

    def create_financing_options(self):
        self.financing_options = [
            FinancingOption("Debt", "Loan at 6% annual interest", 50, "Max $50M per round", "6% annual interest"),
            FinancingOption("VC Funding", "Raise $40M but lose 10% NPV", 40, "Once per game", "10% NPV dilution"),
            FinancingOption("Equity", "Raise capital but dilute 20% NPV", 60, "Once per round", "20% NPV dilution"),
            FinancingOption("IPO", "Raise $100M but lose 30% of final NPV", 100, "Only in Round 4 or 5", "30% NPV penalty")
        ]

    def create_events(self):
        self.events = [
            Event("Economic Downturn", "Economic downturn affects revenue", lambda player: setattr(player, 'cash', player.cash - sum(p.annual_cash_flow for p in player.projects) * 0.15)),
            Event("Cybersecurity Breach", "Security breach costs money", lambda player: setattr(player, 'cash', player.cash - 15) if not any(p.name in ["AI Fraud Prevention", "Blockchain Integration"] for p in player.projects) else None),
            Event("Data Leak Scandal", "Data leak affects user trust", lambda player: player.lose_users(1)),
            Event("Regulatory Fine", "Regulatory issues lead to fine", lambda player: setattr(player, 'cash', player.cash - 10) if not any(p.name == "AI Fraud Prevention" for p in player.projects) else None),
            Event("System Crash", "Major system failure", lambda player: setattr(player, 'skip_next_turn', True)),
            Event("Market Expansion", "New market opportunity", lambda player: player.add_users(0.5)),
            Event("Strategic Partnership", "New partnership opportunity", lambda player: player.receive(10)),
            Event("Talent Acquisition", "Key talent joins company", lambda player: setattr(st.session_state, 'next_project_discount', 0.10)) # Using session state for temporary effect
        ]

    def create_board(self):
        tile_types = {
            "Investment": 8,
            "Financing": 2,
            "Event": 4,
            "Neutral": 4,
            "Special": 2
        }
        positions = list(range(20))
        random.shuffle(positions)

        investment_positions = positions[:tile_types["Investment"]]
        financing_positions = positions[tile_types["Investment"]:tile_types["Investment"]+tile_types["Financing"]]
        event_positions = positions[tile_types["Investment"]+tile_types["Financing"]:tile_types["Investment"]+tile_types["Financing"]+tile_types["Event"]]
        neutral_positions = positions[tile_types["Investment"]+tile_types["Financing"]+tile_types["Event"]:tile_types["Investment"]+tile_types["Financing"]+tile_types["Event"]+tile_types["Neutral"]]
        special_positions = positions[tile_types["Investment"]+tile_types["Financing"]+tile_types["Event"]+tile_types["Neutral"]:]

        self.board = [None] * 20

        for i, pos in enumerate(investment_positions):
            project = self.projects[i % len(self.projects)]
            self.board[pos] = Tile(pos, f"Investment: {project.name}", "Investment", project)

        for i, pos in enumerate(financing_positions):
            self.board[pos] = Tile(pos, "Financing Opportunity", "Financing")

        for i, pos in enumerate(event_positions):
            self.board[pos] = Tile(pos, "Market Event", "Event")

        for i, pos in enumerate(neutral_positions):
            self.board[pos] = Tile(pos, "Revenue Collection", "Neutral")

        self.board[special_positions[0]] = Tile(special_positions[0], "IPO Opportunity", "Special", "IPO")
        self.board[special_positions[1]] = Tile(special_positions[1], "Strategic Decision", "Special", "Strategy")

    def add_player(self, name):
        player = Player(name)
        self.players.append(player)

    def roll_dice(self):
        return random.randint(1, 6)

    def move_player(self, player, steps):
        player.position = (player.position + steps) % len(self.board)
        return self.board[player.position]

    def get_current_tile(self, player):
        return self.board[player.position]

    def handle_investment_tile_ui(self, player, tile):
        project = tile.action
        st.subheader(f"Investment Opportunity: {project.name}")
        st.write(f"Cost: ${project.cost}M")
        st.write(f"Annual Cash Flow: ${project.annual_cash_flow}M for {project.life} years")
        st.write(f"Risk Level: {project.risk_level}")
        st.write(f"User Gain: {project.user_gain}M users")
        st.write(f"NPV: ${project.calculate_npv():.2f}M")
        st.write(f"IRR: {project.calculate_irr()*100:.2f}%")
        st.write(f"Payback Period: {project.calculate_payback_period():.2f} years")

        if project.owner is not None:
            st.write(f"This project is already owned by {project.owner.name}.")
            if st.button("Next"):
                st.session_state.game.next_player_turn()
            return

        if player.can_afford(project.cost):
            if st.button(f"Invest in {project.name} for ${project.cost}M"):
                player.pay(project.cost)
                player.add_project(project, self.current_round)
                player.add_users(project.user_gain)
                st.write(f"You invested in {project.name}!")
                st.session_state.game.next_player_turn()
        else:
            st.write("You cannot afford this project.")
            if st.button("Next"):
                st.session_state.game.next_player_turn()

    def handle_financing_tile_ui(self, player, tile):
        st.subheader("Financing Opportunity")
        available_options = []
        for i, option in enumerate(self.financing_options):
            if option.name == "VC Funding" and player.vc_funding_used:
                continue
            if option.name == "IPO" and self.current_round < 4:
                continue
            available_options.append(option)
            st.write(f"{i+1}. {option.name}: {option.description} ({option.conditions})")

        if not available_options:
            st.write("No financing options available at this time.")
            if st.button("Next"):
                st.session_state.game.next_player_turn()
            return

        selected_option_name = st.selectbox("Choose a financing option:", ["Skip"] + [opt.name for opt in available_options])

        if selected_option_name != "Skip":
            selected_option = next(opt for opt in self.financing_options if opt.name == selected_option_name)
            if selected_option.name == "Debt":
                amount = st.number_input(f"Amount to borrow (max ${selected_option.max_amount}M):", min_value=0, max_value=selected_option.max_amount, step=1)
                if st.button("Take Debt"):
                    if amount > 0:
                        player.receive(amount)
                        player.add_financing(selected_option, amount)
                        st.write(f"You took ${amount}M in debt.")
                        st.session_state.game.next_player_turn()
            elif selected_option.name == "VC Funding":
                if st.button("Get VC Funding"):
                    player.receive(selected_option.max_amount)
                    player.add_financing(selected_option, selected_option.max_amount)
                    st.write(f"You received ${selected_option.max_amount}M in VC funding.")
                    st.session_state.game.next_player_turn()
            elif selected_option.name == "Equity":
                amount = st.number_input(f"Amount to raise (max ${selected_option.max_amount}M):", min_value=0, max_value=selected_option.max_amount, step=1)
                if st.button("Raise Equity"):
                    if amount > 0:
                        player.receive(amount)
                        player.add_financing(selected_option, amount)
                        st.write(f"You raised ${amount}M through equity.")
                        st.session_state.game.next_player_turn()
            elif selected_option.name == "IPO":
                    if st.button("Conduct IPO"):
                        player.receive(selected_option.max_amount)
                        player.add_financing(selected_option, selected_option.max_amount)
                        st.write(f"You conducted an IPO and raised ${selected_option.max_amount}M.")
                        st.session_state.game.next_player_turn()
        else:
            st.write("Invalid choice.")
            if st.button("Next"):
                st.session_state.game.next_player_turn()

    def handle_event_tile_ui(self, player, tile):
        event = random.choice(self.events)
        st.subheader(f"Event: {event.name}")
        st.write(f"Description: {event.description}")
        st.write(f"Impact: {event.impact}")

        event.impact(player)  # Apply the event's effect
        st.session_state.game.next_player_turn()

    def handle_neutral_tile_ui(self, player, tile):
        st.subheader("Revenue Collection")
        revenue = player.collect_project_revenues()
        st.write(f"You collected ${revenue}M in revenue from your projects.")
        st.session_state.game.next_player_turn()

    def handle_special_tile_ui(self, player, tile):
        if tile.action == "IPO":
            if self.current_round >= 4 and not player.ipo_done:
                if st.button("Conduct IPO? (+$100M, -30% final NPV)"):
                    player.receive(100)
                    player.ipo_done = True
                    st.write("You conducted an IPO!")
                    st.session_state.game.next_player_turn()
                else:
                    st.write("You decided not to do an IPO.")
                    st.session_state.game.next_player_turn()
            else:
                st.write("IPO is only available in rounds 4 and 5, once per game.")
                st.session_state.game.next_player_turn()

        elif tile.action == "Strategy":
            st.subheader("Strategic Decision Point")
            if not player.projects:
                st.write("You don't have any projects to make decisions about.")
                st.session_state.game.next_player_turn()
                return

            selected_project_name = st.selectbox("Choose a project:", [p.name for p in player.projects])
            selected_project = next(p for p in player.projects if p.name == selected_project_name)

            strategy_choice = st.radio("Choose a strategy:", ["Skip", "Expand", "Pivot", "Sell"])

            if strategy_choice == "Expand":
                if player.can_afford(20):
                    player.pay(20)
                    selected_project.annual_cash_flow *= 1.5
                    st.write(f"Expanded {selected_project.name}! Cash flow increased.")
                else:
                    st.write("You can't afford to expand.")
                st.session_state.game.next_player_turn()
            elif strategy_choice == "Pivot":
                if player.can_afford(15):
                    player.pay(15)
                    selected_project.annual_cash_flow *= 1.2
                    selected_project.life += 1
                    st.write(f"Pivoted {selected_project.name}! Cash flow and life increased.")
                else:
                    st.write("You can't afford to pivot.")
                st.session_state.game.next_player_turn()
            elif strategy_choice == "Sell":
                recovery = selected_project.cost * 0.5
                player.receive(recovery)
                player.projects.remove(selected_project)
                selected_project.owner = None
                st.write(f"Sold {selected_project.name} for ${recovery}M.")
                st.session_state.game.next_player_turn()
            elif strategy_choice == "Skip":
                st.write("You decided not to make a strategic decision.")
                st.session_state.game.next_player_turn()

    def handle_end_of_round(self):
        st.subheader(f"End of Round {self.current_round}")

        bankrupt_players = []
        for player in self.players:
            if player.debt > 0:
                if not player.pay_debt_interest():
                    st.write(f"{player.name} is bankrupt and out of the game!")
                    bankrupt_players.append(player)

        for player in bankrupt_players:
            self.players.remove(player)

        self.show_scoreboard()

        self.current_round += 1
        if self.current_round > self.num_rounds:
            self.game_over = True
            self.end_game()
        else:
            st.write(f"Starting Round {self.current_round}...")

    def show_scoreboard(self):
        st.subheader("Current Standings")
        headers = ["Player", "Cash ($M)", "Users (M)", "Projects", "NPV ($M)", "Debt ($M)"]
        table_data = []
        for player in self.players:
            npv = player.calculate_total_npv(self.current_round)
            table_data.append([player.name, f"{player.cash:.2f}", f"{player.users:.2f}", len(player.projects), f"{npv:.2f}", f"{player.debt:.2f}"])
        st.table(tabulate(table_data, headers=headers, tablefmt="grid"))

    def end_game(self):
        st.subheader("GAME OVER")
        final_scores = []
        for player in self.players:
            npv = player.calculate_total_npv(self.current_round)
            npv_score = npv * 0.4
            users_score = player.users * 0.3
            cash_score = player.cash * 0.1
            strategic_score = 0
            if player.ipo_done:
                strategic_score += 10
            strategic_score += len(player.projects) * 2
            strategic_score *= 0.2
            total_score = npv_score + users_score + cash_score + strategic_score
            final_scores.append((player, total_score, npv, player.users, player.cash, strategic_score))

        final_scores.sort(key=lambda x: x[1], reverse=True)

        st.subheader("Final Results")
        headers = ["Rank", "Player", "Total Score", "NPV ($M)", "Users (M)", "Cash ($M)", "Strategic"]
        table_data = []
        for i, (player, score, npv, users, cash, strategic) in enumerate(final_scores):
            table_data.append([i+1, player.name, f"{score:.2f}", f"{npv:.2f}", f"{users:.2f}", f"{cash:.2f}", f"{strategic:.2f}"])
        st.table(tabulate(table_data, headers=headers, tablefmt="grid"))

        winner = final_scores[0][0]
        st.write(f"Congratulations, {winner.name}! You are the winner!")

    def next_player_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        if self.current_player_index == 0:
            self.handle_end_of_round()
        if not self.game_over:
            self.play_turn()

    def play_turn(self):
        if not self.players:  # Add this check
            return  # Exit if there are no players
        player = self.players[self.current_player_index]
        st.subheader(f"{player.name}'s Turn (Round {self.current_round})")
        st.write(f"Current Position: {player.position}")
        st.write(f"Cash: ${player.cash}M")
        st.write(f"Users: {player.users}M")
        st.write(f"Projects: {len(player.projects)}")

        if player.skip_next_turn:
            st.write(f"{player.name}'s turn is skipped due to system crash.")
            player.skip_next_turn = False
            self.next_player_turn()
            return

        if st.button("Roll Dice"):
            dice_roll = self.roll_dice()
            st.write(f"You rolled a {dice_roll}!")
            tile = self.move_player(player, dice_roll)
            st.write(f"You landed on: {tile.name} (Position {tile.position})")

            if tile.tile_type == "Investment":
                self.handle_investment_tile_ui(player, tile)
            elif tile.tile_type == "Financing":
                self.handle_financing_tile_ui(player, tile)
            elif tile.tile_type == "Event":
                self.handle_event_tile_ui(player, tile)
            elif tile.tile_type == "Neutral":
                self.handle_neutral_tile_ui(player, tile)
            elif tile.tile_type == "Special":
                self.handle_special_tile_ui(player, tile)
        else:
            st.stop()
 # prevent the rest of the code from running until the button is clicked

def main():
    st.title("Finopoly")

    if 'game' not in st.session_state:
        st.session_state.game = Finopoly()
        st.session_state.player_names = []
        st.session_state.num_players = 0

    if st.session_state.num_players == 0:
        st.session_state.num_players = st.number_input("Enter number of players (3-5):", min_value=3, max_value=5, step=1)
        if st.session_state.num_players > 0:
            for i in range(st.session_state.num_players):
                name = st.text_input(f"Enter name for Player {i+1}:")
                st.session_state.player_names.append(name)
            if all(name != "" for name in st.session_state.player_names):
                for name in st.session_state.player_names:
                    st.session_state.game.add_player(name)
                st.write("Starting Finopoly Game!")
                st.write("Each player starts with $100M and 1M users.")
                st.write("The goal is to maximize your company value over 5 rounds.")
                st.session_state.game.play_turn()
    else:
        if not st.session_state.game.game_over:
            st.session_state.game.play_turn()
        else:
            st.session_state.game.end_game()

if __name__ == "__main__":
    main()
