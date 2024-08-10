import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, roc_auc_score, f1_score
from imblearn.over_sampling import RandomOverSampler
from imblearn.pipeline import Pipeline
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import ConfusionMatrixDisplay

def classificationHashtag(data_df):
    try:
        print("Step 1: Converting data to DataFrame")
        df = pd.DataFrame(data_df)
        print("DataFrame shape:", df.shape)
    except Exception as e:
        print(f"An error occurred: {e}")
    try:
        print("\nStep 2: Filling missing values")
        # Create a column to indicate if the industry value was missing
        df['industry_missing'] = df['industry'].isna()

        # Fill missing values in 'industry' column with a placeholder
        df['industry'].fillna('Unknown', inplace=True)

        # Drop the original 'industry_missing' column
        df.drop(columns=['industry_missing'], inplace=True)
        print("Missing values filled and auxiliary column removed")
    except Exception as e:
        print(f"An error occurred: {e}")
    try:
        print("\nStep 3: Printing actual number of industry types")
        industry_types = df['industry'].unique()
        actual_num_clusters = len(industry_types)
        print(f'Actual number of industry types: {actual_num_clusters}')
        print(industry_types)
    except Exception as e:
        print(f"An error occurred: {e}")
    try:
        print("\nStep 4: One-hot encoding categorical columns")
        # One-hot encode categorical columns, excluding 'hashtag'
        df = pd.get_dummies(df, columns=['country_name', 'industry', 'trend_type', 'is_new'])
        print(df.head())
    except Exception as e:
        print(f"An error occurred: {e}")

    # Step 5: Separate data with 'industry_Unknown' as True
    print("\nStep 5: Separating data with 'industry_Unknown' as True")
    # Filter df to get rows where 'industry_Unknown' is True
    unknown_data = df[df['industry_Unknown'] == True]
    known_data = df[df['industry_Unknown'] == False]

    # Drop the 'industry_Unknown' column
    unknown_data = unknown_data.drop(columns=['industry_Unknown'])
    known_data = known_data.drop(columns=['industry_Unknown'])

    # Step 6: Prepare features and labels
    industry_columns = [col for col in df.columns if col.startswith('industry_') and col != 'industry_Unknown']

    # Drop non-numeric columns if any
    X = known_data.drop(columns=industry_columns)  # Drop all 'industry_' columns except 'industry_Unknown'
    X = X.select_dtypes(include=[np.number])  # Keep only numeric columns

    # Use LabelEncoder to convert string labels to numerical indices
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(known_data[industry_columns].idxmax(axis=1))

    # Step 7: Visualize using PCA
    print("\nStep 7: Visualizing industry classes")
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X)

    # Define markers for different classes
    markers = ['o', 's', 'D', '^', 'v', '<', '>']  # Circle, Square, Diamond, Triangle_up, Triangle_down, Triangle_left, Triangle_right
    classes = np.unique(y)  # Use np.unique to get unique class labels

    for i, cls in enumerate(classes):
        plt.scatter(X_pca[y == cls, 0], X_pca[y == cls, 1], marker=markers[i % len(markers)], label=label_encoder.classes_[cls])

    plt.title("Industry Classes Visualization")
    plt.xlabel("PCA Component 1")
    plt.ylabel("PCA Component 2")
    plt.legend(loc='best')
    plt.show()

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Define parameter grid
    param_grid = {
        'n_estimators': [100, 200],
        'learning_rate': [0.01, 0.1],
        'max_depth': [3, 5],
        'min_child_weight': [1, 5],
        'gamma': [0, 0.1],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0]
    }

    # Create XGBClassifier with default parameters
    xgb = XGBClassifier(eval_metric='mlogloss')

    # Grid search
    grid_search = GridSearchCV(xgb, param_grid, scoring='f1_weighted', cv=3, verbose=1)
    grid_search.fit(X_train, y_train)

    # Best parameters and score
    print("Best parameters:", grid_search.best_params_)
    print("Best score:", grid_search.best_score_)

    # Use the best model to predict
    best_model = grid_search.best_estimator_

    # Step 10: Evaluating the model on test data
    print("\nStep 10: Evaluating the model on test data")
    y_pred = best_model.predict(X_test)

    # Get unique class labels present in y_test
    unique_classes_test = np.unique(y_test)

    # Filter label_encoder.classes_ to include only classes present in y_test
    target_names = [label_encoder.classes_[i] for i in unique_classes_test]

    print(classification_report(y_test, y_pred, target_names=target_names))  # Use filtered target_names

    # Step 11: Predict industry for unknown data
    print("\nStep 11: Predicting industry for unknown data")
    X_unknown = unknown_data.select_dtypes(include=[np.number])  # Ensure only numeric columns are used
    y_unknown_pred = best_model.predict(X_unknown)

    # Decode predicted labels back to original class names
    predicted_industries = label_encoder.inverse_transform(y_unknown_pred)

    # Update unknown data with predicted industries
    unknown_data['predicted_industry'] = predicted_industries

    # Convert predicted industries to one-hot encoding
    unknown_data_encoded = pd.get_dummies(unknown_data[['predicted_industry']], prefix='industry')

    # Ensure all industry columns are present
    for col in industry_columns:
        if col not in unknown_data_encoded.columns:
            unknown_data_encoded[col] = 0

    # Reorder columns to match industry_columns
    unknown_data_encoded = unknown_data_encoded[industry_columns]

    # Assign predicted industries to the original unknown_data
    unknown_data[industry_columns] = unknown_data_encoded

    # Step 13: Combine known and predicted data
    # Convert industry columns in unknown_data to boolean
    for column in known_data.columns:
        if column.startswith('industry_') and column not in unknown_data.columns:
            unknown_data[column] = 0

    # Ensure all columns are aligned
    aligned_known_data = known_data.copy()
    aligned_unknown_data = unknown_data.copy()

    # Convert integer industry columns to boolean in unknown_data
    for col in [col for col in aligned_unknown_data.columns if col.startswith('industry_')]:
        aligned_unknown_data[col] = aligned_unknown_data[col].astype(bool)

    # Combine DataFrames
    combined_data = pd.concat([aligned_known_data, aligned_unknown_data], ignore_index=True)

    print("\nStep 13: Data without missing industry:")
    print(combined_data.shape)

    print("Sample predicted industries:")
    print(unknown_data[['hashtag', 'predicted_industry']].head())
    print(classification_report(y_test, y_pred, target_names=target_names, zero_division=1))

    # Print unique labels in y_test and y_pred
    print("Unique labels in y_test:", np.unique(y_test))
    print("Unique labels in y_pred:", np.unique(y_pred))

    # Generate confusion matrix using unique labels from both y_test and y_pred
    labels = np.unique(np.concatenate([y_test, y_pred]))  # Combine labels from both y_test and y_pred

    cm = confusion_matrix(y_test, y_pred, labels=labels)

    # Display confusion matrix
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(cmap=plt.cm.Blues)
    plt.show()

    # Check the length of predictions and unknown data
    print(f"Length of predictions (y_pred): {len(y_pred)}")
    print(f"Length of unknown_data: {len(unknown_data)}")

    # Predict and align
    y_pred = best_model.predict(X_unknown)

    # Reset index to align
    unknown_data = unknown_data.reset_index(drop=True)
    combined_data = unknown_data.copy()
    combined_data['predicted_industry'] = np.nan

    # Check if lengths match
    if len(y_pred) == len(unknown_data):
        combined_data['predicted_industry'] = label_encoder.inverse_transform(y_pred)
    else:
        print("Length mismatch: Predictions cannot be aligned with data.")
        print(f"Length of y_pred: {len(y_pred)}")
        print(f"Length of unknown_data: {len(unknown_data)}")

    # Combine known_data and unknown_data
    combined_data = pd.concat([known_data, unknown_data], ignore_index=True)

    # Fill missing 'predicted_industry' values with 'Unknown'
    combined_data['predicted_industry'].fillna('Unknown', inplace=True)

    print("Data with 'predicted_industry' filled:")

    print("########################")
    print(combined_data.shape)
    print("########################")

    data = combined_data
    # Verify DataFrame structure and columns
    print("Data structure overview:")
    print(data.head())
    print("Column names:", data.columns)

    # Ensure the column names are strings
    data.columns = data.columns.map(str)

    # Check if 'predicted_industry' exists
    if 'predicted_industry' not in data.columns:
        print("Error: 'predicted_industry' column is missing.")
    else:
        # Fill missing 'predicted_industry' values with 'Unknown'
        data['predicted_industry'].fillna('Unknown', inplace=True)

        # Identify industry columns
        industry_columns = [col for col in data.columns if col.startswith('industry_')]
        print(f"Industry Columns: {industry_columns}")

        # Initialize topics_chart dictionary
        topics_chart = {
            'topics': industry_columns,
            'counts': {},
            'hashtags': {},
            'wordclouds': {}
        }

        # Process each industry column
        for col in industry_columns:
            # industry_name = col.replace('industry_', '')
            industry_name = col

            # Get counts for each industry from known data
            industry_count = int(data[col].sum())
            if col not in topics_chart['counts']:
                topics_chart['counts'][industry_name] = 0  # Initialize count

            topics_chart['counts'][industry_name] += industry_count

            # Get hashtags for each industry
            industry_hashtags = data[data[col] == 1]['hashtag'].tolist()
            if industry_name not in topics_chart['hashtags']:
                topics_chart['hashtags'][industry_name] = industry_hashtags
            else:
                topics_chart['hashtags'][industry_name].extend(industry_hashtags)

            # Create wordcloud data for each industry
            industry_wordcloud = []
            for _, row in data[data[col] == 1].iterrows():
                value = int(row['video_views']) * int(row['publish_count'])
                industry_wordcloud.append({'hashtag': row['hashtag'], 'value': value})

            if industry_name not in topics_chart['wordclouds']:
                topics_chart['wordclouds'][industry_name] = industry_wordcloud
            else:
                topics_chart['wordclouds'][industry_name].extend(industry_wordcloud)

        # Process unknown data
        if 'predicted_industry' in data.columns:
            predicted_counts = data['predicted_industry'].value_counts()
            for industry_name, count in predicted_counts.items():
                if industry_name != "Unknown":
                    if industry_name not in topics_chart['counts']:
                        topics_chart['counts'][industry_name] = count
                    else:
                        topics_chart['counts'][industry_name] += count

                    # Get hashtags and wordcloud data for unknown data
                    industry_hashtags = data[data['predicted_industry'] == industry_name]['hashtag'].tolist()
                    if industry_name not in topics_chart['hashtags']:
                        topics_chart['hashtags'][industry_name] = industry_hashtags
                    else:
                        topics_chart['hashtags'][industry_name].extend(industry_hashtags)

                    industry_wordcloud = []
                    for _, row in data[data['predicted_industry'] == industry_name].iterrows():
                        value = int(row['video_views']) * int(row['publish_count'])
                        industry_wordcloud.append({'hashtag': row['hashtag'], 'value': value})

                    if industry_name not in topics_chart['wordclouds']:
                        topics_chart['wordclouds'][industry_name] = industry_wordcloud
                    else:
                        topics_chart['wordclouds'][industry_name].extend(industry_wordcloud)

        # Remove any duplicate entries in 'topics'
        topics_chart['topics'] = list(set(topics_chart['topics']))
        return topics_chart