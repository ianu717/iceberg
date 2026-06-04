import json
import pickle
import numpy as np

from src.utils import extract_profile_selection
from src.config import MODEL_DIR

def load_model_package():
    with open(MODEL_DIR / 'modelo_clustering.pkl', 'rb') as f:
        model_package = pickle.load(f)
        return model_package

def build_feature_vector(preferencias, duracion, compania, model_package):

    prefs = model_package['prefs']
    duration_map = model_package['duration_map']
    companion_map = model_package['companion_map']
    scaler = model_package['scaler']

    assert len(preferencias) == 3, "Deben ser exactamente 3 preferencias"
    assert all(p in prefs for p in preferencias), f"Preferencia no válida: {preferencias}"
    assert duracion in duration_map, f"Duración no válida: {duracion}"
    assert compania in companion_map, f"Compañía no válida: {compania}"

    # Vector de preferencias binario
    vector_prefs = [1 if p in preferencias else 0 for p in prefs]

    # duration y companion como valores ordinales (mismo rango que los sintéticos)
    vector_ctx = [duration_map[duracion], companion_map[compania]]
    vector = np.array(vector_prefs + vector_ctx).reshape(1, -1)

    vector_scaled = scaler.transform(vector)

    return vector_scaled

def predict_cluster(x, model_package):
    kmeans = model_package['kmeans']
    nombre_por_cluster = model_package['nombre_por_cluster']
    cluster_to_categorias = model_package['cluster_to_categorias']
    cluster_id = int(kmeans.predict(x)[0])
    nombre = nombre_por_cluster[cluster_id]
    categorias = cluster_to_categorias[nombre]

    return {
        'cluster_id': cluster_id,
        'perfil': nombre,
        'subcategorias': categorias['subcategorias'],
        'vibes': categorias['vibes'],
    }


def predict_user_profile(preferences: list[str], duration: str, companion: str) -> dict:
    model_package = load_model_package()
    x = build_feature_vector(preferences, duration, companion, model_package)
    prediction = predict_cluster(x, model_package)
    return prediction

if __name__ == '__main__':
    query_array = ['culture','local_favorites','walking_tours', 'threedays', 'partner']
    preferences, duration, companion = extract_profile_selection(query_array)
    profile = predict_user_profile(preferences, duration, companion)

    print(f'Preferencias: {preferences}')
    print(f'Duracion: {duration}')
    print(f'Comañia: {companion}\n')
    print('Perfil predicho:')
    print(json.dumps(profile, indent=4, ensure_ascii=False))



