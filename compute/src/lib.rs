use pyo3::prelude::*;
use pyo3::types::PyList;

fn ensure_equal_lengths(a: &[f64], b: &[f64]) -> PyResult<()> {
    if a.len() != b.len() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Vectors must have the same length",
        ));
    }
    if a.is_empty() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Vectors must not be empty",
        ));
    }
    Ok(())
}

fn cosine(a: &[f64], b: &[f64]) -> f64 {
    let mut dot = 0.0_f64;
    let mut norm_a = 0.0_f64;
    let mut norm_b = 0.0_f64;

    for (&ai, &bi) in a.iter().zip(b.iter()) {
        dot += ai * bi;
        norm_a += ai * ai;
        norm_b += bi * bi;
    }

    if norm_a == 0.0 || norm_b == 0.0 {
        return 0.0;
    }
    dot / (norm_a.sqrt() * norm_b.sqrt())
}

#[pyfunction]
fn ping() -> &'static str {
    "kadas-ai-compute-ready"
}

#[pyfunction]
fn cosine_similarity(a: Vec<f64>, b: Vec<f64>) -> PyResult<f64> {
    ensure_equal_lengths(&a, &b)?;
    Ok(cosine(&a, &b))
}

#[pyfunction]
fn top_k_cosine(query: Vec<f64>, candidates: Vec<Vec<f64>>, k: usize) -> PyResult<Vec<(usize, f64)>> {
    if query.is_empty() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "query vector must not be empty",
        ));
    }
    if candidates.is_empty() {
        return Ok(Vec::new());
    }

    let mut scored: Vec<(usize, f64)> = Vec::with_capacity(candidates.len());
    for (index, candidate) in candidates.iter().enumerate() {
        ensure_equal_lengths(&query, candidate)?;
        scored.push((index, cosine(&query, candidate)));
    }

    scored.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    let keep = k.min(scored.len());
    scored.truncate(keep);
    Ok(scored)
}

#[pyfunction]
fn bbox_area(min_x: f64, min_y: f64, max_x: f64, max_y: f64) -> PyResult<f64> {
    if min_x >= max_x || min_y >= max_y {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Invalid bbox: min values must be lower than max values",
        ));
    }
    Ok((max_x - min_x) * (max_y - min_y))
}

#[pyfunction]
fn haversine_distance_m(lon1: f64, lat1: f64, lon2: f64, lat2: f64) -> f64 {
    let radius_m = 6_371_000.0_f64;
    let phi1 = lat1.to_radians();
    let phi2 = lat2.to_radians();
    let dphi = (lat2 - lat1).to_radians();
    let dlambda = (lon2 - lon1).to_radians();

    let a = (dphi / 2.0).sin().powi(2) + phi1.cos() * phi2.cos() * (dlambda / 2.0).sin().powi(2);
    let c = 2.0 * a.sqrt().atan2((1.0 - a).sqrt());
    radius_m * c
}

#[pyfunction]
fn pairwise_haversine_matrix(points: Vec<(f64, f64)>, py: Python<'_>) -> PyResult<Py<PyList>> {
    if points.is_empty() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "points must not be empty",
        ));
    }
    let n = points.len();
    let mut matrix: Vec<Vec<f64>> = vec![vec![0.0; n]; n];

    for i in 0..n {
        for j in (i + 1)..n {
            let (lon1, lat1) = points[i];
            let (lon2, lat2) = points[j];
            let d = haversine_distance_m(lon1, lat1, lon2, lat2);
            matrix[i][j] = d;
            matrix[j][i] = d;
        }
    }

    Ok(PyList::new(py, matrix)?.into())
}

#[pymodule]
fn kadas_ai_compute(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(ping, module)?)?;
    module.add_function(wrap_pyfunction!(cosine_similarity, module)?)?;
    module.add_function(wrap_pyfunction!(top_k_cosine, module)?)?;
    module.add_function(wrap_pyfunction!(bbox_area, module)?)?;
    module.add_function(wrap_pyfunction!(haversine_distance_m, module)?)?;
    module.add_function(wrap_pyfunction!(pairwise_haversine_matrix, module)?)?;
    Ok(())
}
