from sklearn.feature_extraction.text import CountVectorizer
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from utils.common import tokenize_prune_stem
from typing import Dict, List
import numpy as np
import logging
import os


logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


def get_doc2vec_embeddngs(
    save_dir: str,
    document_list: List[str],
    stemming_map: Dict[str, str],
    num_epochs: int,
    vector_size: int,
    training_regime: int,
) -> np.ndarray:
    # Tokenize
    cv = CountVectorizer(tokenizer=lambda text: tokenize_prune_stem(
        text, stemming_map=stemming_map))
    cv_tokenizer = cv.build_tokenizer()
    document_list = [cv_tokenizer(document) for document in document_list]

    # Convert to TaggedDocument and train
    print('Training Doc2Vec...')
    tagged_document_list = [TaggedDocument(
        doc, [i]) for i, doc in enumerate(document_list)]
    doc2vec_model = _train_doc2vec(
        docs=tagged_document_list,
        vector_size=vector_size,
        num_epochs=num_epochs,
        training_regime=training_regime,
    )
    _save_for_inference(doc2vec_model, os.path.join(save_dir, 'doc2vec.model'))

    return _infer_document_embeddings(doc2vec_model, document_list)


def _train_doc2vec(docs: List[TaggedDocument], vector_size: int, num_epochs: int, training_regime: int) -> Doc2Vec:
    model = Doc2Vec(vector_size=vector_size, window=5, min_count=2,
                    workers=4, epochs=num_epochs, dm=training_regime)
    model.build_vocab(docs)
    model.train(docs, total_examples=model.corpus_count, epochs=num_epochs)
    return model


def _infer_document_embeddings(model: Doc2Vec, doc_list: List[List[str]]) -> np.ndarray:
    """
    NOTE: Inference is not deterministic therefore representations will vary between calls
    Returns a 2D array with shape (num_docs, embedding_dimension)
    """
    print('Infering document embeddings..')
    return np.array([model.infer_vector(doc) for doc in doc_list])


def _save_for_inference(model: Doc2Vec, path_name: str) -> None:
    model.delete_temporary_training_data(
        keep_doctags_vectors=True, keep_inference=True)
    model.save(path_name)
