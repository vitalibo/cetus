#!/usr/bin/env python3

import argparse

import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(description='Generate a dataset for testing')
parser.add_argument('--frac', type=float, default=0.1, help='Fraction of the dataset to generate')
parser.add_argument('--seed', type=int, default=42, help='Random seed')
parser.add_argument('output', type=str, help='Output file')
args = parser.parse_args()

products = ['Laptop', 'Tablet', 'Smartphone', 'Monitor', 'Keyboard', 'Mouse', 'Printer', 'Camera', 'Headphones']
regions = ['North America', 'Europe', 'Asia', 'South America', 'Australia', 'Africa']
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
categories = ['Electronics', 'Accessories', 'Office Supplies', 'Furniture', 'Appliances']
customer_segments = ['Consumer', 'Corporate', 'Small Business', 'Home Office', 'Government']
sales_channels = ['Online', 'Offline', 'Direct Sales', 'Reseller', 'Retail']

data = []
for product in products:
    for region in regions:
        for month in months:
            for category in categories:
                for customer_segment in customer_segments:
                    for sales_channel in sales_channels:
                        data.append([
                            product, region, month, category, customer_segment, sales_channel,
                            np.round(np.random.uniform(100, 10000), 2),
                            np.round(np.random.uniform(10, 5000), 2),
                            np.random.randint(1, 100)
                        ])

df = pd.DataFrame(data, columns=[
    'Product', 'Region', 'Month', 'Category', 'Customer Segment', 'Sales Channel', 'Sales', 'Profit', 'Quantity'
])

df = df.sample(frac=args.frac, random_state=args.seed)

df.to_csv(args.output, index=False)
