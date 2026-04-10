import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import json
import yaml
from collections import defaultdict
import re
from dateutil import parser

class BookstoreAnalyzer:
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.orders = None
        self.users = None
        self.books = None
        self.results = {}
    
    def load_and_clean_data(self):
        """Load and clean all data files with proper type handling"""
        try:
            # Load YAML books data
            print(f"Loading books from {self.data_folder}/books.yaml...")
            with open(f"{self.data_folder}/books.yaml", 'r', encoding='utf-8') as file:
                books_data = yaml.safe_load(file)
            
            # Convert YAML to DataFrame
            if isinstance(books_data, list):
                self.books = pd.DataFrame(books_data)
            elif isinstance(books_data, dict):
                if 'books' in books_data:
                    self.books = pd.DataFrame(books_data['books'])
                else:
                    self.books = pd.DataFrame([books_data])
            
            # Load Parquet orders data
            self.orders = pd.read_parquet(f"{self.data_folder}/orders.parquet")
            
            # Load CSV users data
            self.users = pd.read_csv(f"{self.data_folder}/users.csv")
            
            print(f"Loaded data successfully:")
            print(f"- Books: {len(self.books)} records")
            print(f"- Orders: {len(self.orders)} records") 
            print(f"- Users: {len(self.users)} records")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
        
        # Clean all data with proper type handling
        self.clean_orders()
        self.clean_users()
        self.clean_books()
        
        return True
    
    def parse_timestamp_robust(self, timestamp_str):
        """Parse various timestamp formats robustly"""
        if pd.isna(timestamp_str) or timestamp_str == '':
            return None
        
        try:
            timestamp_str = str(timestamp_str).strip()
            
            # Remove problematic parts
            timestamp_str = re.sub(r'\s+[AP]\.M\.', '', timestamp_str)
            timestamp_str = re.sub(r'[,\s]+', ' ', timestamp_str).strip()
            
            return parser.parse(timestamp_str, fuzzy=True)
            
        except Exception:
            return None
    
    def clean_orders(self):
        """Clean orders data with proper type conversion"""
        print(f"\nCleaning orders data...")
        print(f"Orders columns: {list(self.orders.columns)}")
        
        # Handle duplicates
        initial_count = len(self.orders)
        self.orders = self.orders.drop_duplicates()
        print(f"Removed {initial_count - len(self.orders)} duplicate orders")
        
        # Parse timestamps and extract date components
        if 'timestamp' in self.orders.columns:
            print("Parsing timestamps...")
            self.orders['timestamp'] = self.orders['timestamp'].apply(self.parse_timestamp_robust)
            
            # Remove unparseable timestamps
            before_count = len(self.orders)
            self.orders = self.orders.dropna(subset=['timestamp'])
            print(f"Removed {before_count - len(self.orders)} rows with unparseable timestamps")
            
            # Extract date components as requested
            self.orders['date'] = self.orders['timestamp'].dt.date
            self.orders['year'] = self.orders['timestamp'].dt.year
            self.orders['month'] = self.orders['timestamp'].dt.month
            self.orders['day'] = self.orders['timestamp'].dt.day
            
            print(f"Successfully parsed {len(self.orders)} timestamps")
        
        # Handle missing values in critical columns
        for col in ['quantity', 'unit_price']:
            if col in self.orders.columns:
                before_count = len(self.orders)
                self.orders = self.orders.dropna(subset=[col])
                print(f"Removed {before_count - len(self.orders)} rows with missing {col}")
        
        # Ensure proper data types
        if 'quantity' in self.orders.columns:
            self.orders['quantity'] = pd.to_numeric(self.orders['quantity'], errors='coerce')
            self.orders = self.orders.dropna(subset=['quantity'])
        
        # Convert currency to USD and add paid_price column
        if 'unit_price' in self.orders.columns:
            self.orders['unit_price_usd'] = self.orders['unit_price'].apply(self.convert_to_usd)
            # Add paid_price column as requested: quantity * unit_price
            self.orders['paid_price'] = self.orders['quantity'] * self.orders['unit_price_usd']
            print(f"Added paid_price column for {len(self.orders)} orders")
        
        # Convert IDs to proper types
        for col in ['user_id', 'book_id', 'id']:
            if col in self.orders.columns:
                self.orders[col] = self.orders[col].astype(str)
        
        print(f"Orders cleaned: {len(self.orders)} records remaining")
    
    def convert_to_usd(self, price):
        """Convert price to USD (€1 = $1.2 as specified)"""
        if pd.isna(price):
            return 0.0
        
        if isinstance(price, str):
            price_clean = re.sub(r'[^\d.,€$]', '', price)
            
            try:
                # Handle European format
                if ',' in price_clean and '.' in price_clean:
                    if price_clean.rfind(',') > price_clean.rfind('.'):
                        price_clean = price_clean.replace('.', '').replace(',', '.')
                
                numeric_price = float(price_clean.replace(',', '').replace('€', '').replace('$', ''))
                
                # Convert EUR to USD as specified: €1 = $1.2
                if '€' in str(price) or 'EUR' in str(price).upper():
                    return numeric_price * 1.2
                else:
                    return numeric_price
                    
            except ValueError:
                return 0.0
        
        try:
            return float(price)
        except (ValueError, TypeError):
            return 0.0
    
    def clean_users(self):
        """Clean users data with proper type handling"""
        print(f"\nCleaning users data...")
        print(f"Users columns: {list(self.users.columns)}")
        
        # Handle duplicates
        self.users = self.users.drop_duplicates()
        
        # Ensure user_id is string type
        if 'user_id' in self.users.columns:
            self.users['user_id'] = self.users['user_id'].astype(str)
        elif 'id' in self.users.columns:
            self.users['user_id'] = self.users['id'].astype(str)
        
        # Handle missing values in text fields
        text_cols = ['name', 'email', 'phone', 'address', 'first_name', 'last_name']
        for col in text_cols:
            if col in self.users.columns:
                self.users[col] = self.users[col].fillna('').astype(str)
        
        print(f"Users cleaned: {len(self.users)} records")
    
    def clean_books(self):
        """Clean books data with proper type handling"""
        print(f"\nCleaning books data...")
        print(f"Books columns: {list(self.books.columns)}")
        
        if self.books.empty:
            print("Warning: Books dataframe is empty!")
            return
        
        # Handle duplicates
        self.books = self.books.drop_duplicates()
        
        # Handle columns that start with ':'
        column_mapping = {}
        for col in self.books.columns:
            if col.startswith(':'):
                new_col = col[1:]  # Remove the ':'
                column_mapping[col] = new_col
        
        if column_mapping:
            self.books = self.books.rename(columns=column_mapping)
            print(f"Renamed columns: {column_mapping}")
        
        # Ensure book_id is string type
        if 'book_id' in self.books.columns:
            self.books['book_id'] = self.books['book_id'].astype(str)
        elif 'id' in self.books.columns:
            self.books['book_id'] = self.books['id'].astype(str)
        else:
            self.books['book_id'] = self.books.index.astype(str)
        
        # Handle authors field
        if 'authors' in self.books.columns:
            self.books['authors'] = self.books['authors'].apply(self.normalize_authors)
        elif 'author' in self.books.columns:
            self.books['authors'] = self.books['author'].apply(self.normalize_authors)
        else:
            self.books['authors'] = ''
        
        print(f"Books cleaned: {len(self.books)} records")
        print(f"Sample authors: {self.books['authors'].head().tolist()}")
    
    def normalize_authors(self, authors):
        """Normalize authors field to handle various formats"""
        if pd.isna(authors):
            return ''
        
        if isinstance(authors, list):
            return ', '.join([str(author).strip() for author in authors if str(author).strip()])
        elif isinstance(authors, str):
            return authors.strip()
        else:
            return str(authors).strip()
    
    def compute_daily_revenue(self):
        """Compute daily revenue and find top 5 days by revenue"""
        print(f"\nComputing daily revenue...")
        
        if 'date' not in self.orders.columns or 'paid_price' not in self.orders.columns:
            print("Warning: Cannot compute daily revenue")
            self.results['top_5_days'] = []
            self.results['daily_revenue'] = []
            return
        
        # Group by date and sum paid_price as requested
        daily_revenue = self.orders.groupby('date')['paid_price'].sum().reset_index()
        daily_revenue = daily_revenue.sort_values('paid_price', ascending=False)
        
        # Get top 5 days by revenue
        top_5_days = daily_revenue.head(5).copy()
        # Format dates as YYYY-MM-DD as requested
        top_5_days['date_str'] = top_5_days['date'].astype(str)
        
        self.results['top_5_days'] = top_5_days[['date_str', 'paid_price']].to_dict('records')
        
        # For chart - sort by date
        daily_revenue_sorted = daily_revenue.sort_values('date')
        daily_revenue_sorted['date_str'] = daily_revenue_sorted['date'].astype(str)
        self.results['daily_revenue'] = daily_revenue_sorted[['date_str', 'paid_price']].to_dict('records')
        
        if not top_5_days.empty:
            print(f"Top revenue day: {top_5_days.iloc[0]['date_str']} with ${top_5_days.iloc[0]['paid_price']:.2f}")
    
    def find_unique_users(self):
        """Find unique users considering aliases (only one field can change)"""
        print(f"\nFinding unique users with alias reconciliation...")
        
        if self.users.empty:
            self.results['unique_users'] = 0
            self.results['user_groups'] = {}
            return 0
        
        user_groups = defaultdict(set)
        users_list = self.users.to_dict('records')
        processed_users = set()
        
        for i, user1 in enumerate(users_list):
            user_id1 = user1.get('user_id', str(i))
            
            if user_id1 not in processed_users:
                user_groups[user_id1].add(user_id1)
                processed_users.add(user_id1)
                
                # Find users with only one field different (aliases)
                for j, user2 in enumerate(users_list[i+1:], i+1):
                    user_id2 = user2.get('user_id', str(j))
                    
                    if user_id2 not in processed_users and self.users_similar_one_field(user1, user2):
                        user_groups[user_id1].add(user_id2)
                        processed_users.add(user_id2)
        
        unique_users_count = len(user_groups)
        self.results['unique_users'] = unique_users_count
        self.results['user_groups'] = {k: list(v) for k, v in user_groups.items()}
        
        print(f"Found {unique_users_count} unique users from {len(users_list)} total records")
        return unique_users_count
    
    def users_similar_one_field(self, user1, user2):
        """Check if users are similar with only one field different"""
        comparison_fields = ['name', 'email', 'phone', 'address']
        differences = 0
        compared_fields = 0
        
        for field in comparison_fields:
            if field in user1 and field in user2:
                val1 = str(user1[field]).lower().strip()
                val2 = str(user2[field]).lower().strip()
                
                if val1 and val2:  # Only compare non-empty values
                    compared_fields += 1
                    if val1 != val2:
                        differences += 1
        
        # Users are similar if exactly one field is different and at least 2 fields compared
        return differences == 1 and compared_fields >= 2
    
    def find_unique_author_sets(self):
        """Find unique sets of authors (e.g., John, Paul, John&Paul = 3 sets)"""
        print(f"\nFinding unique author sets...")
        
        if self.books.empty or 'authors' not in self.books.columns:
            print("Warning: No authors column found")
            self.results['unique_author_sets'] = 0
            self.results['author_sets_list'] = []
            return 0
        
        author_sets = set()
        processed_books = 0
        
        for _, book in self.books.iterrows():
            authors_str = book['authors']
            if authors_str and str(authors_str).strip() and str(authors_str).strip().lower() != 'nan':
                processed_books += 1
                # Split authors by various delimiters
                if ',' in str(authors_str):
                    authors = [author.strip() for author in str(authors_str).split(',')]
                elif ';' in str(authors_str):
                    authors = [author.strip() for author in str(authors_str).split(';')]
                elif ' and ' in str(authors_str):
                    authors = [author.strip() for author in str(authors_str).split(' and ')]
                elif '&' in str(authors_str):
                    authors = [author.strip() for author in str(authors_str).split('&')]
                else:
                    authors = [str(authors_str).strip()]
                
                # Create sorted tuple for consistent comparison
                authors = tuple(sorted([author for author in authors if author and author.lower() != 'nan']))
                if authors:
                    author_sets.add(authors)
        
        unique_author_sets = len(author_sets)
        self.results['unique_author_sets'] = unique_author_sets
        self.results['author_sets_list'] = [list(author_set) for author_set in author_sets]
        
        print(f"Processed {processed_books} books with authors")
        print(f"Found {unique_author_sets} unique author sets")
        if unique_author_sets > 0:
            print(f"Sample author sets: {list(author_sets)[:3]}")
        
        return unique_author_sets
    
    def find_most_popular_author(self):
        """Find most popular author by sold book count"""
        print(f"\nFinding most popular author by book sales...")
        
        if self.orders.empty or self.books.empty:
            print("Warning: Orders or books data is empty")
            self.results['most_popular_author'] = {'authors': [], 'books_sold': 0}
            return
        
        # Find common column for merging
        book_id_col = 'book_id' if 'book_id' in self.orders.columns and 'book_id' in self.books.columns else 'id'
        
        if book_id_col not in self.orders.columns or book_id_col not in self.books.columns:
            print("Warning: Cannot merge orders and books - no common ID column")
            self.results['most_popular_author'] = {'authors': [], 'books_sold': 0}
            return
        
        # Merge orders with books
        print(f"Merging on column: {book_id_col}")
        orders_books = self.orders.merge(self.books, on=book_id_col, how='left')
        print(f"Merged {len(orders_books)} records")
        
        author_sales = defaultdict(int)
        
        for _, row in orders_books.iterrows():
            if 'authors' in row and row['authors'] and str(row['authors']).strip() and str(row['authors']).strip().lower() != 'nan':
                authors_str = str(row['authors'])
                
                # Parse authors
                if ',' in authors_str:
                    authors = [author.strip() for author in authors_str.split(',')]
                elif ';' in authors_str:
                    authors = [author.strip() for author in authors_str.split(';')]
                elif ' and ' in authors_str:
                    authors = [author.strip() for author in authors_str.split(' and ')]
                elif '&' in authors_str:
                    authors = [author.strip() for author in authors_str.split('&')]
                else:
                    authors = [authors_str.strip()]
                
                authors = tuple(sorted([author for author in authors if author and author.lower() != 'nan']))
                if authors:
                    quantity = row.get('quantity', 1)
                    if pd.notna(quantity):
                        author_sales[authors] += int(quantity)
        
        print(f"Found sales data for {len(author_sales)} author sets")
        
        if author_sales:
            # ИСПРАВЛЕНО: x[1] вместо x[1]
            most_popular = max(author_sales.items(), key=lambda x: x[1])
            self.results['most_popular_author'] = {
                'authors': list(most_popular[0]),
                'books_sold': most_popular[1]
            }
            print(f"Most popular author(s): {list(most_popular[0])} with {most_popular[1]} books sold")
        else:
            print("No author sales data found")
            self.results['most_popular_author'] = {'authors': [], 'books_sold': 0}
    
    def find_top_customer(self):
        """Find top customer by total spending with all aliases"""
        print(f"\nFinding top customer by total spending...")
        
        if self.orders.empty:
            self.results['top_customer'] = {'user_ids': [], 'total_spending': 0}
            return
        
        # Group by user_id and sum spending
        user_spending = self.orders.groupby('user_id')['paid_price'].sum().reset_index()
        user_spending = user_spending.sort_values('paid_price', ascending=False)
        
        if not user_spending.empty:
            top_user_id = str(user_spending.iloc[0]['user_id'])
            top_spending = user_spending.iloc[0]['paid_price']
            
            # Find all aliases for this user
            user_groups = self.results.get('user_groups', {})
            top_customer_aliases = []
            
            for main_id, group in user_groups.items():
                if top_user_id in group:
                    top_customer_aliases = list(group)
                    break
            
            if not top_customer_aliases:
                top_customer_aliases = [top_user_id]
            
            self.results['top_customer'] = {
                'user_ids': top_customer_aliases,
                'total_spending': float(top_spending)
            }
            
            print(f"Top customer: {top_customer_aliases} with ${top_spending:.2f} total spending")
        else:
            self.results['top_customer'] = {'user_ids': [], 'total_spending': 0}
    
    def plot_daily_revenue(self, save_path=None):
        """Plot simple line chart of daily revenue using matplotlib"""
        daily_revenue_data = self.results.get('daily_revenue', [])
        
        if not daily_revenue_data:
            print("No daily revenue data to plot")
            return None
        
        df = pd.DataFrame(daily_revenue_data)
        df['date'] = pd.to_datetime(df['date_str'])
        df = df.sort_values('date')
        
        # Simple line chart as requested
        plt.figure(figsize=(12, 6))
        plt.plot(df['date'], df['paid_price'], marker='o', linewidth=2)
        plt.title(f'Daily Revenue - {self.data_folder}', fontsize=14, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Revenue (USD)')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {save_path}")
        
        return plt
    
    def analyze_all(self):
        """Run complete analysis"""
        print(f"\n{'='*50}")
        print(f"Analyzing data from {self.data_folder}...")
        print(f"{'='*50}")
        
        if not self.load_and_clean_data():
            return None
        
        # Run all analyses as requested
        self.compute_daily_revenue()
        self.find_unique_users()
        self.find_unique_author_sets()
        self.find_most_popular_author()
        self.find_top_customer()
        
        print(f"\nAnalysis complete for {self.data_folder}!")
        return self.results

def analyze_all_datasets():
    """Analyze all three datasets separately as requested"""
    datasets = ['DATA1', 'DATA2', 'DATA3']
    all_results = {}
    
    os.makedirs('charts', exist_ok=True)
    os.makedirs('results', exist_ok=True)
    
    for dataset in datasets:
        print(f"\n{'#'*60}")
        print(f"PROCESSING {dataset}")
        print(f"{'#'*60}")
        
        analyzer = BookstoreAnalyzer(f'data/{dataset}')
        results = analyzer.analyze_all()
        
        if results:
            all_results[dataset] = results
            
            # Save individual results
            with open(f'results/{dataset}_results.json', 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Plot and save chart for each dataset
            chart_path = f'charts/{dataset}_daily_revenue.png'
            analyzer.plot_daily_revenue(chart_path)
            plt.show()  # Show the chart
            plt.close()
            
            # Print summary in required format
            print(f"\n{dataset} RESULTS:")
            print(f"Top 5 days by revenue (YYYY-MM-DD format):")
            for i, day in enumerate(results.get('top_5_days', [])[:5], 1):
                print(f"  {i}. {day['date_str']}: ${day['paid_price']:.2f}")
            
            print(f"Number of unique users: {results.get('unique_users', 0)}")
            print(f"Number of unique sets of authors: {results.get('unique_author_sets', 0)}")
            
            popular_author = results.get('most_popular_author', {})
            if popular_author.get('authors'):
                print(f"Most popular author(s): {', '.join(popular_author['authors'])}")
            else:
                print("Most popular author(s): No data")
            
            top_customer = results.get('top_customer', {})
            if top_customer.get('user_ids'):
                print(f"Best buyer (with aliases): {top_customer['user_ids']}")
            else:
                print("Best buyer: No data")
    
    # Save combined results
    with open('results/all_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    # Generate data for dashboard
    with open('dashboard_data.js', 'w') as f:
        f.write(f"const analysisResults = {json.dumps(all_results, indent=2, default=str)};")
    
    print(f"\n{'='*60}")
    print("ALL ANALYSES COMPLETE!")
    print("Results saved to 'results/' directory")
    print("Charts saved to 'charts/' directory")
    print("Dashboard data saved to 'dashboard_data.js'")
    print(f"{'='*60}")
    
    return all_results

if __name__ == "__main__":
    # Install required packages
    try:
        import yaml
        import pyarrow
        from dateutil import parser
    except ImportError as e:
        print(f"Please install required packages: pip install PyYAML pyarrow python-dateutil")
        exit(1)
    
    # Run analysis
    results = analyze_all_datasets()