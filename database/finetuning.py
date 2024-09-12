import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel, Trainer, TrainingArguments, DataCollatorForLanguageModeling
from torch.utils.data import Dataset
import pandas as pd
from sklearn.model_selection import train_test_split
import warnings
from transformers import EarlyStoppingCallback
from torch.cuda.amp import autocast

# Filter warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="Unnecessary tokenizer pad_token_id")

class KeywordDataset(Dataset):
    def __init__(self, tokenized_data):
        self.input_ids = [x['input_ids'].squeeze() for x in tokenized_data]
        self.labels = [x['input_ids'].squeeze() for x in tokenized_data]
        self.attention_masks = [x['attention_mask'].squeeze() for x in tokenized_data]

    def __len__(self):
        return len(self.input_ids)

    def __getitem__(self, idx):
        return {
            'input_ids': self.input_ids[idx],
            'labels': self.labels[idx],
            'attention_mask': self.attention_masks[idx]
        }

def fine_tune_gpt2(prompt):
    # Define the file path (fixed)
    file_path = './dataset/nv dataset.csv'
    
    # Load and preprocess the dataset
    df = pd.read_csv(file_path, sep=';')

    def clean_data(row):
        keyword = row['Keyword']
        search_volume = row['Search Volume'].replace('.', '').replace(',', '')
        cpc = row['CPC'].replace(',', '.')

        if pd.isnull(keyword) or pd.isnull(search_volume) or pd.isnull(cpc):
            return None

        return f"Keyword: {keyword.strip()}, Search Volume: {search_volume.strip()}, CPC: {cpc.strip()}"

    df['input_text'] = df.apply(clean_data, axis=1)
    df.dropna(subset=['input_text'], inplace=True)

    # Train-test split
    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)

    # Load tokenizer and model
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    tokenizer.pad_token = tokenizer.eos_token

    def tokenize_function(examples):
        return tokenizer(
            examples['input_text'],
            truncation=True,
            padding='max_length',
            max_length=128,
            return_tensors='pt'
        )

    train_tokenized = train_df['input_text'].apply(lambda x: tokenize_function({'input_text': x}))
    val_tokenized = val_df['input_text'].apply(lambda x: tokenize_function({'input_text': x}))

    train_dataset = KeywordDataset(train_tokenized)
    val_dataset = KeywordDataset(val_tokenized)

    model = GPT2LMHeadModel.from_pretrained('gpt2')
    model.to('cuda' if torch.cuda.is_available() else 'cpu')
    model.config.pad_token_id = model.config.eos_token_id
    model.resize_token_embeddings(len(tokenizer))

    # Training arguments
    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=5,
        per_device_train_batch_size=4,
        evaluation_strategy="steps",
        eval_steps=1000,
        logging_steps=200,
        load_best_model_at_end=True,
        fp16=True,
        learning_rate=2e-5,
        weight_decay=0.01,
        warmup_steps=500,
        save_steps=5000,
        save_total_limit=2,
        logging_dir='./logs',
        report_to="none",
        gradient_accumulation_steps=4,
        logging_first_step=True,
        dataloader_num_workers=4
    )

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
    )

    with autocast():
        trainer.train()

    # Save model and tokenizer
    model.save_pretrained('./gpt2-finetuned')
    tokenizer.save_pretrained('./gpt2-finetuned')

    # Tokenize input
    inputs = tokenizer(prompt, return_tensors='pt', padding=True, truncation=True, max_length=128).to(model.device)

    # Generate output
    output = model.generate(
        inputs['input_ids'],
        attention_mask=inputs['attention_mask'],
        max_length=256,
        do_sample=True,
        temperature=0.5,
        top_k=20,
        top_p=0.9,
        num_beams=10,
        no_repeat_ngram_size=3,
        repetition_penalty=1.3,
        early_stopping=True,
        pad_token_id=tokenizer.eos_token_id
    )

    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
    return generated_text
