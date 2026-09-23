"""Field names and domain lists for competition attachments."""

DOMAIN_COLS = [
    "train_the_pile_arxiv",
    "train_the_pile_freelaw",
    "train_the_pile_nih_exporter",
    "train_the_pile_pubmed_central",
    "train_the_pile_wikipedia_en",
    "train_the_pile_dm_mathematics",
    "train_the_pile_github",
    "train_the_pile_philpapers",
    "train_the_pile_stackexchange",
    "train_the_pile_enron_emails",
    "train_the_pile_gutenberg_pg_19",
    "train_the_pile_pile_cc",
    "train_the_pile_ubuntu_irc",
    "train_the_pile_europarl",
    "train_the_pile_hackernews",
    "train_the_pile_pubmed_abstracts",
    "train_the_pile_uspto_backgrounds",
]

LOSS_COLS = [
    "metric/the_pile_arxiv_val_loss",
    "metric/the_pile_freelaw_val_loss",
    "metric/the_pile_pubmed_central_val_loss",
    "metric/the_pile_wikipedia_en_val_loss",
    "metric/the_pile_dm_mathematics_val_loss",
    "metric/the_pile_github_val_loss",
    "metric/the_pile_stackexchange_val_loss",
    "metric/the_pile_gutenberg_pg_19_val_loss",
    "metric/the_pile_pile_cc_val_loss",
    "metric/the_pile_ubuntu_irc_val_loss",
    "metric/the_pile_hackernews_val_loss",
    "metric/the_pile_pubmed_abstracts_val_loss",
    "metric/the_pile_uspto_backgrounds_val_loss",
]

QUALITY_METRICS = [
    "fineweb_edu",
    "fluency_en",
    "modernbert_cleanliness",
    "modernbert_readability",
    "modernbert_reasoning",
    "modernbert_professionalism",
    "dsir_books",
    "dsir_wiki",
    "dsir_math",
    "qurater",
    "ad_en",
    "rps_doc_word_count",
    "rps_doc_num_sentences",
    "rps_doc_unigram_entropy",
    "rps_doc_frac_unique_words",
    "rps_doc_frac_no_alph_words",
    "rps_doc_frac_chars_top_2gram",
    "rps_doc_frac_chars_top_3gram",
    "rps_lines_uppercase_letter_fraction",
    "rps_lines_ending_with_terminal_punctution_mark",
    "rps_lines_numerical_chars_fraction",
    "rps_doc_mean_word_length",
]

# Higher raw value = lower quality (invert after min-max)
NEGATIVE_METRICS = {
    "ad_en",
    "rps_doc_frac_no_alph_words",
    "rps_doc_frac_chars_top_2gram",
    "rps_doc_frac_chars_top_3gram",
    "rps_lines_uppercase_letter_fraction",
    "rps_lines_numerical_chars_fraction",
}

LIST_METRICS = {
    "fineweb_edu",
    "fluency_en",
    "modernbert_cleanliness",
    "modernbert_readability",
    "modernbert_reasoning",
    "modernbert_professionalism",
    "dsir_books",
    "dsir_wiki",
    "dsir_math",
}

POSITIVE_QUALITY_GROUP = {
    "fineweb_edu",
    "fluency_en",
    "modernbert_cleanliness",
    "modernbert_readability",
    "modernbert_reasoning",
    "modernbert_professionalism",
    "dsir_books",
    "dsir_wiki",
    "dsir_math",
    "qurater",
}
