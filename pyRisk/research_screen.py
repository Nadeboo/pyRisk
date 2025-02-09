# research_screen.py

import tkinter as tk
from tkinter import ttk
from research import ResearchTier, ResearchType, ResearchManager

class ResearchScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.setup_widgets()

    def setup_widgets(self):
        # Main title
        title_frame = tk.Frame(self.frame)
        title_frame.pack(fill=tk.X, pady=20)
        tk.Label(title_frame, text="Research Management", font=("Arial", 24)).pack(expand=True)

        # Create three-panel layout
        self.create_layout_frames()
        self.setup_player_buttons()
        self.setup_research_spreadsheet()

    def create_layout_frames(self):
        # Left panel for player buttons
        self.player_frame = tk.Frame(self.frame, width=150, bg='lightgrey')
        self.player_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.player_frame.pack_propagate(False)

        # Right panel for research spreadsheet
        self.spreadsheet_frame = tk.Frame(self.frame)
        self.spreadsheet_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    def setup_player_buttons(self):
        tk.Label(self.player_frame, text="Players", font=("Arial", 12, "bold"), bg='lightgrey').pack(pady=10)
        
        for player in self.app.players:
            # Create frame for player button with color indicator
            btn_frame = tk.Frame(self.player_frame, bg='lightgrey')
            btn_frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Color indicator
            color_box = tk.Frame(
                btn_frame, 
                bg='#{:02x}{:02x}{:02x}'.format(*player.color),
                width=10, 
                height=10
            )
            color_box.pack(side=tk.LEFT, padx=5)
            color_box.pack_propagate(False)
            
            # Player button
            btn = tk.Button(
                btn_frame,
                text=player.name,
                command=lambda p=player: self.show_tier_menu(p)
            )
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def show_tier_menu(self, player):
        """Show popup menu with research tiers"""
        menu = tk.Menu(self.frame, tearoff=0)
        
        for tier in ResearchTier:
            submenu = tk.Menu(menu, tearoff=0)
            menu.add_cascade(label=f"Tier {tier.value}", menu=submenu)
            
            # Add research options for this tier
            for research in ResearchType.get_by_tier(tier):
                submenu.add_command(
                    label=research.display_name,
                    command=lambda p=player, r=research: self.add_research(p, r)
                )
        
        # Show the menu at the current mouse position
        menu.post(self.frame.winfo_pointerx(), self.frame.winfo_pointery())

    def add_research(self, player, research_type):
        """Add research to player and update display"""
        player.complete_research(research_type)
        self.update_research_spreadsheet()
        
        # Update game screen mirror if it exists
        if hasattr(self.app.current_screen, 'update_mirror_panels'):
            self.app.current_screen.update_mirror_panels()

    def setup_research_spreadsheet(self):
        """Create the research spreadsheet view"""
        # Create headers
        ttk.Label(self.spreadsheet_frame, text="Research Type", font=("Arial", 10, "bold")).grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        for col, player in enumerate(self.app.players, start=1):
            player_frame = ttk.Frame(self.spreadsheet_frame)
            player_frame.grid(row=0, column=col, padx=5, pady=5)
            
            # Color indicator
            color_box = tk.Frame(
                player_frame,
                bg='#{:02x}{:02x}{:02x}'.format(*player.color),
                width=10,
                height=10
            )
            color_box.pack(side=tk.LEFT, padx=2)
            color_box.pack_propagate(False)
            
            ttk.Label(player_frame, text=player.name).pack(side=tk.LEFT)

        # Add research rows
        current_row = 1
        for tier in ResearchTier:
            # Add tier header
            ttk.Label(
                self.spreadsheet_frame, 
                text=f"Tier {tier.value}", 
                font=("Arial", 9, "bold")
            ).grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.W)
            current_row += 1
            
            # Add research items for this tier
            for research in ResearchType.get_by_tier(tier):
                ttk.Label(
                    self.spreadsheet_frame,
                    text=research.display_name
                ).grid(row=current_row, column=0, padx=15, pady=2, sticky=tk.W)
                
                # Add indicators for each player
                for col, player in enumerate(self.app.players, start=1):
                    has_research = player.has_research(research)
                    label = ttk.Label(
                        self.spreadsheet_frame,
                        text="✓" if has_research else ""
                    )
                    label.grid(row=current_row, column=col, padx=5, pady=2)
                
                current_row += 1

    def update_research_spreadsheet(self):
        """Clear and redraw the research spreadsheet"""
        for widget in self.spreadsheet_frame.winfo_children():
            widget.destroy()
        self.setup_research_spreadsheet()

    def destroy(self):
        self.frame.destroy()