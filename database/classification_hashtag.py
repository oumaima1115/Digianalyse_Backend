import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedShuffleSplit
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, roc_auc_score, f1_score
from imblearn.over_sampling import RandomOverSampler
from imblearn.pipeline import Pipeline
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import ConfusionMatrixDisplay
import hashlib
import matplotlib.colors as mcolors

def classificationHashtag(data_df):
    try:
        # Convert data to DataFrame
        df = pd.DataFrame(data_df)

        # Fill missing values
        df['industry_missing'] = df['industry'].isna()
        df['industry'] = df['industry'].fillna('Unknown')

        # One-hot encoding categorical columns
        df = pd.get_dummies(df, columns=['country_name', 'industry', 'trend_type', 'is_new'])

        # Separate data with 'industry_Unknown' as True
        unknown_data = df[df['industry_Unknown'] == True].drop(columns=['industry_Unknown'])
        known_data = df[df['industry_Unknown'] == False].drop(columns=['industry_Unknown'])

        # Prepare features and labels
        industry_columns = [col for col in df.columns if col.startswith('industry_') and col != 'industry_Unknown' and col != 'industry_missing']
        X = known_data.drop(columns=industry_columns).select_dtypes(include=[np.number])

        # Filter out classes with too few samples before encoding
        min_samples = 2
        label_encoder = LabelEncoder()
        y_raw = known_data[industry_columns].idxmax(axis=1)
        y_raw_counts = y_raw.value_counts()
        y_filtered = y_raw[y_raw.isin(y_raw_counts[y_raw_counts >= min_samples].index)]

        # Apply label encoding
        y = label_encoder.fit_transform(y_filtered)
        X_filtered = X.loc[y_filtered.index]

        # Split the data into training and testing sets using stratified split
        split = StratifiedShuffleSplit(n_splits=1, test_size=0.3, random_state=42)
        for train_index, test_index in split.split(X_filtered, y):
            X_train, X_test = X_filtered.iloc[train_index], X_filtered.iloc[test_index]
            y_train, y_test = y[train_index], y[test_index]

        # Handle imbalanced classes
        ros = RandomOverSampler(random_state=42)
        X_resampled, y_resampled = ros.fit_resample(X_train, y_train)

        # Train the model with GridSearchCV
        param_grid = {
            'n_estimators': [100, 200],
            'learning_rate': [0.01, 0.1],
            'max_depth': [3, 5],
            'min_child_weight': [1, 5],
            'gamma': [0, 0.1],
            'subsample': [0.8, 1.0],
            'colsample_bytree': [0.8, 1.0]
        }

        xgb = XGBClassifier(eval_metric='mlogloss')
        grid_search = GridSearchCV(xgb, param_grid, scoring='f1_weighted', cv=3, verbose=3, error_score='raise')
        grid_search.fit(X_resampled, y_resampled)

        best_model = grid_search.best_estimator_

        # Evaluate the model on test data
        y_pred = best_model.predict(X_test)
        unique_classes_test = np.unique(y_test)
        target_names = [label_encoder.classes_[i] for i in unique_classes_test]

        # Predict industry for unknown data
        X_unknown = unknown_data.select_dtypes(include=[np.number])
        y_unknown_pred = best_model.predict(X_unknown)
        predicted_industries = label_encoder.inverse_transform(y_unknown_pred)

        unknown_data['predicted_industry'] = predicted_industries
        unknown_data_encoded = pd.get_dummies(unknown_data[['predicted_industry']], prefix='industry')

        for col in industry_columns:
            if col not in unknown_data_encoded.columns:
                unknown_data_encoded[col] = 0

        unknown_data_encoded = unknown_data_encoded[industry_columns]
        unknown_data[industry_columns] = unknown_data_encoded

        # Combine known and predicted data
        for column in known_data.columns:
            if column.startswith('industry_') and column not in unknown_data.columns:
                unknown_data[column] = 0

        combined_data = pd.concat([known_data, unknown_data], ignore_index=True)

        # Industry topics chart generation
        topics_chart = {
            'topics': industry_columns,
            'colors': {},
            'percentages': {},
            'counts': {},
            'hashtags': {},
            'wordclouds': {}
        }

        def generate_random_color(industry_name, used_colors, max_attempts=10):
            color_palette = list(mcolors.CSS4_COLORS.values())
            hash_value = abs(hash(industry_name)) % len(color_palette)

            attempts = 0
            while attempts < max_attempts:
                color = color_palette[hash_value]
                if color not in used_colors:
                    used_colors.add(color)
                    return color
                hash_value = (hash_value + 1) % len(color_palette)
                attempts += 1

            new_color = mcolors.CSS4_COLORS[list(mcolors.CSS4_COLORS.keys())[hash_value % len(mcolors.CSS4_COLORS)]]
            used_colors.add(new_color)
            return new_color

        # Process each industry column
        used_colors = set()
        for industry in industry_columns:
            color = generate_random_color(industry, used_colors)
            topics_chart['colors'][industry] = color

        # Additional logic for topics chart data
        # Additional logic for topics chart data
        for col in industry_columns:
            industry_name = col

            # Get counts for each industry from combined data
            industry_count = int(combined_data[col].sum())
            topics_chart['counts'][industry_name] = industry_count

            # Get hashtags for each industry
            industry_hashtags = combined_data[combined_data[col] == 1]['hashtag'].tolist()
            topics_chart['hashtags'][industry_name] = industry_hashtags

            # Create wordcloud data for each industry
            industry_wordcloud = []
            for _, row in combined_data[combined_data[col] == 1].iterrows():
                value = int(row['video_views']) * int(row['publish_count'])
                industry_wordcloud.append({'hashtag': row['hashtag'], 'value': value})

            topics_chart['wordclouds'][industry_name] = industry_wordcloud

        # Calculate the total count of all industries
        total_count = sum(topics_chart['counts'].values())

        # Calculate the percentages for each industry and add them to the topics_chart
        for industry, count in topics_chart['counts'].items():
            percentage = (count / total_count) * 100
            topics_chart['percentages'][industry] = percentage

        # Round percentages to two decimal places for better readability (optional)
        for industry in topics_chart['percentages']:
            topics_chart['percentages'][industry] = round(topics_chart['percentages'][industry], 2)

        return topics_chart

    except Exception as e:
        print("Error:", e)