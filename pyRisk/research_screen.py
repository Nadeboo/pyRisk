# research_screen.py

import tkinter as tk
from tkinter import ttk, messagebox
from research import ResearchTier, ResearchType

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
        
        # Create player list in left panel
        tk.Label(self.player_frame, text="Players", font=("Arial", 12, "bold"), 
                bg='lightgrey').pack(pady=10)
        
        # Create buttons for each player
        for player in self.app.players:
            player_btn = tk.Frame(self.player_frame, bg='lightgrey')
            player_btn.pack(fill=tk.X, padx=5, pady=2)
            
            # Color indicator
            color_box = tk.Frame(
                player_btn,
                bg='#{:02x}{:02x}{:02x}'.format(*player.color),
                width=15,
                height=15
            )
            color_box.pack(side=tk.LEFT, padx=5)
            color_box.pack_propagate(False)
            
            # Player name with right-click binding
            player_label = tk.Label(player_btn, text=player.name, bg='lightgrey')
            player_label.pack(side=tk.LEFT)
            
            # Bind right-click to show research menu
            player_label.bind('<Button-3>', lambda e, p=player: self.show_tier_menu(e, p))
            color_box.bind('<Button-3>', lambda e, p=player: self.show_tier_menu(e, p))
        
        # Setup the research spreadsheet
        self.setup_research_spreadsheet()

    def create_layout_frames(self):
        # Left panel for player list
        self.player_frame = tk.Frame(self.frame, width=150, bg='lightgrey')
        self.player_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.player_frame.pack_propagate(False)

        # Right panel for research spreadsheet
        self.spreadsheet_frame = tk.Frame(self.frame)
        self.spreadsheet_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    def setup_research_spreadsheet(self):
        """Create the research spreadsheet view with separated research paths"""
        # Clear existing widgets
        for widget in self.spreadsheet_frame.winfo_children():
            widget.destroy()
            
        # Configure main frame
        self.spreadsheet_frame.configure(relief=tk.SOLID, bd=1)
        
        # Create header row
        header_row = 0
        player_col = 0
        
        # Player header
        tk.Label(self.spreadsheet_frame, text="PLR", relief=tk.SOLID, bd=1, width=15,
                anchor='w', padx=5).grid(row=header_row, column=player_col, sticky="nsew")

        # Get research types by path
        steel_research = sorted(ResearchType.get_by_path('steel'), key=lambda r: (r.tier.value, r.code))
        magic_research = sorted(ResearchType.get_by_path('magic'), key=lambda r: (r.tier.value, r.code))
        
        # Create research type headers
        current_col = player_col + 1
        
        # Steel Path Header
        steel_header = tk.Label(self.spreadsheet_frame, text="Steel Path", relief=tk.SOLID, bd=1,
                              bg='lightgray', font=('Arial', 12, 'bold'))
        steel_header.grid(row=0, column=current_col, 
                         columnspan=len(steel_research), sticky="nsew")
        
        # Steel research headers
        for research in steel_research:
            header = tk.Label(self.spreadsheet_frame, text=research.code, relief=tk.SOLID, bd=1,
                            width=16, bg='#e8e8e8', font=("Arial", 8))
            header.grid(row=1, column=current_col, sticky="nsew")
            header.bind('<Button-3>', lambda e, r=research: self.show_research_info(e, r))
            current_col += 1

        # Separator column
        separator = tk.Frame(self.spreadsheet_frame, width=20, bg='gray')
        separator.grid(row=0, column=current_col, rowspan=100, sticky="ns")
        current_col += 1
        
        # Magic Path Header
        magic_start_col = current_col
        magic_header = tk.Label(self.spreadsheet_frame, text="Magic Path", relief=tk.SOLID, bd=1,
                              bg='#e6e6fa', font=('Arial', 12, 'bold'))
        magic_header.grid(row=0, column=current_col,
                         columnspan=len(magic_research), sticky="nsew")
        
        # Magic research headers
        for research in magic_research:
            header = tk.Label(self.spreadsheet_frame, text=research.code, relief=tk.SOLID, bd=1,
                            width=16, bg='#e8e8e8', font=("Arial", 8))
            header.grid(row=1, column=current_col, sticky="nsew")
            header.bind('<Button-3>', lambda e, r=research: self.show_research_info(e, r))
            current_col += 1

        # Add player rows
        current_row = 2
        for player in self.app.players:
            # Player name and color cell
            player_frame = tk.Frame(self.spreadsheet_frame, relief=tk.SOLID, bd=1)
            player_frame.grid(row=current_row, column=player_col, sticky="nsew")
            
            # Color indicator
            color_box = tk.Frame(player_frame, 
                               bg='#{:02x}{:02x}{:02x}'.format(*player.color),
                               width=15, height=15)
            color_box.pack(side=tk.LEFT, padx=2, pady=2)
            color_box.pack_propagate(False)
            
            # Bind right-click menu
            color_box.bind('<Button-3>', lambda e, p=player: self.show_tier_menu(e, p))
            
            # Add cells for steel research
            col = player_col + 1
            for research in steel_research:
                cell = tk.Frame(self.spreadsheet_frame, relief=tk.SOLID, bd=1, bg='#f8f8f8')
                cell.grid(row=current_row, column=col, sticky="nsew")
                
                # Create a clickable frame for the entire cell
                click_frame = tk.Frame(cell, bg='#f8f8f8')
                click_frame.pack(fill=tk.BOTH, expand=True)
                
                if player.has_research(research):
                    checkmark = tk.Label(click_frame, text="✓", bg='#f8f8f8')
                    checkmark.pack(padx=2, pady=2)
                    # Add tooltip
                    self.add_tooltip(checkmark, "Click to remove research")
                    # Bind click events
                    checkmark.bind('<Button-1>', lambda e, p=player, r=research: self.toggle_research(p, r))
                    click_frame.bind('<Button-1>', lambda e, p=player, r=research: self.toggle_research(p, r))
                else:
                    # Empty cell is still clickable to add research
                    click_frame.bind('<Button-1>', lambda e, p=player, r=research: self.toggle_research(p, r))
                
                col += 1

            # Skip separator column
            col += 1
            
            # Add cells for magic research
            for research in magic_research:
                cell = tk.Frame(self.spreadsheet_frame, relief=tk.SOLID, bd=1, bg='#f8f8ff')
                cell.grid(row=current_row, column=col, sticky="nsew")
                
                # Create a clickable frame for the entire cell
                click_frame = tk.Frame(cell, bg='#f8f8ff')
                click_frame.pack(fill=tk.BOTH, expand=True)
                
                if player.has_research(research):
                    checkmark = tk.Label(click_frame, text="✓", bg='#f8f8ff')
                    checkmark.pack(padx=2, pady=2)
                    # Add tooltip
                    self.add_tooltip(checkmark, "Click to remove research")
                    # Bind click events
                    checkmark.bind('<Button-1>', lambda e, p=player, r=research: self.toggle_research(p, r))
                    click_frame.bind('<Button-1>', lambda e, p=player, r=research: self.toggle_research(p, r))
                else:
                    # Empty cell is still clickable to add research
                    click_frame.bind('<Button-1>', lambda e, p=player, r=research: self.toggle_research(p, r))
                
                col += 1
            
            current_row += 1

        # Configure grid weights
        self.spreadsheet_frame.grid_columnconfigure(player_col, weight=1)
        for col in range(player_col + 1, current_col):
            self.spreadsheet_frame.grid_columnconfigure(col, weight=1)

    def add_tooltip(self, widget, text):
        """Add a tooltip to a widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, bg="lightyellow", relief="solid", borderwidth=1)
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            widget.tooltip = tooltip
            widget.bind('<Leave>', lambda e: hide_tooltip())
            
        widget.bind('<Enter>', show_tooltip)

    def show_research_info(self, event, research):
        """Show information about the research type when right-clicking header"""
        menu = tk.Menu(self.frame, tearoff=0)
        menu.add_command(label=f"Research: {research.display_name}", state=tk.DISABLED)
        menu.add_command(label=f"Path: {research.path.title()}", state=tk.DISABLED)
        menu.add_command(label=f"Tier: {research.tier.value}", state=tk.DISABLED)
        menu.tk_popup(event.x_root, event.y_root)

    def show_tier_menu(self, event, player):
        """Show popup menu with research tiers separated by path"""
        menu = tk.Menu(self.frame, tearoff=0)
        
        # Steel Path submenu
        steel_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Steel Path", menu=steel_menu)
        
        # Magic Path submenu
        magic_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Magic Path", menu=magic_menu)
        
        # Add research by tier to appropriate path menu
        for tier in ResearchTier:
            steel_tier_menu = tk.Menu(steel_menu, tearoff=0)
            magic_tier_menu = tk.Menu(magic_menu, tearoff=0)
            
            steel_research = [r for r in ResearchType.get_by_tier(tier) if r.path == 'steel']
            magic_research = [r for r in ResearchType.get_by_tier(tier) if r.path == 'magic']
            
            if steel_research:
                steel_menu.add_cascade(label=f"Tier {tier.value}", menu=steel_tier_menu)
                for research in steel_research:
                    steel_tier_menu.add_command(
                        label=research.display_name,
                        command=lambda p=player, r=research: self.add_research(p, r)
                    )
                    
            if magic_research:
                magic_menu.add_cascade(label=f"Tier {tier.value}", menu=magic_tier_menu)
                for research in magic_research:
                    magic_tier_menu.add_command(
                        label=research.display_name,
                        command=lambda p=player, r=research: self.add_research(p, r)
                    )
        
        menu.tk_popup(event.x_root, event.y_root)

    def add_research(self, player, research_type):
        """Add research to player and update display"""
        player.complete_research(research_type)
        self.setup_research_spreadsheet()
        
        # Update game screen mirror if it exists
        if hasattr(self.app.current_screen, 'update_mirror_panels'):
            self.app.current_screen.update_mirror_panels()

    def toggle_research(self, player, research):
        """Toggle research status for a player"""
        if player.has_research(research):
            # Ask for confirmation before removing research
            if messagebox.askyesno("Confirm Remove Research", 
                                f"Remove {research.display_name} research from {player.name}?"):
                player.research_manager.completed_research.remove(research)
                self.setup_research_spreadsheet()
                
                if hasattr(self.app.current_screen, 'update_mirror_panels'):
                    self.app.current_screen.update_mirror_panels()
        else:
            # Add research
            self.add_research(player, research)

    def update_display(self):
        """Update the entire display"""
        self.setup_widgets()

    def destroy(self):
        """Clean up when closing the screen"""
        self.frame.destroy()