import scipy.stats as stats
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
import secrets
from collections import Counter

def generate_csprng_numbers(n_qubits: int, n_shots: int) -> list[int]:
    max_val = 2**n_qubits
    return [secrets.randbelow(max_val) for _ in range(n_shots)]

def chi_square_test_for_csprng(n_qubits: int, n_shots: int, alpha: float = 0.05):
    # 1. Generowanie danych z CSPRNG
    numbers = generate_csprng_numbers(n_qubits, n_shots)
    counts = Counter(numbers)
    
    # 2. Zliczenia obserbowane dla wszystkich możliwych wartości [0, 2^n - 1]
    num_states = 2**n_qubits
    observed_counts = [counts.get(i, 0) for i in range(num_states)]
    
    # 3. Wartość oczekiwana
    expected_count = n_shots / num_states
    expected_counts = [expected_count] * num_states
    
    # 4. Statystyka Chi-kwadrat
    chi2_stat, p_value = stats.chisquare(f_obs=observed_counts, f_exp=expected_counts)
    critical_value = stats.chi2.ppf(1 - alpha, num_states - 1)
    
    print(f"--- TEST CHI-KWADRAT CSPRNG ({n_qubits} bitów, shots: {n_shots}) ---")
    print(f"Statystyka Chi2: {chi2_stat:.4f} | p-value: {p_value:.4f}")
    return chi2_stat, p_value

def generate_dynamic_circuit(n_qubits: int):
    qc = QuantumCircuit(n_qubits)
    for n in range(n_qubits):
        qc.h(n)
    return qc

def get_results(qc: QuantumCircuit, n_shots: int):
    sampler = StatevectorSampler()
    result = sampler.run([qc], shots=n_shots).result()
    return result

def generate_and_measure(n_qubits: int, n_shots: int):
    dqc = generate_dynamic_circuit(n_qubits)
    dqc.measure_all()
    results = get_results(dqc, n_shots)
    return results

def bitstrings_to_numbers(results: list[str]):
    bitstrings = results[0].data.meas.get_bitstrings()
    numbers = [int(b, 2) for b in bitstrings]
    return numbers

def sample_test(n_bits: int, tests: list[int]):
    results = []
    for test in tests:
        result = generate_and_measure(n_bits, test)
        result = result[0].data.meas.get_counts()
        results.append(result)
    return results

def statictical_distribution(n_bits: int, tests: list[int]):
    results = sample_test(n_bits, tests)
    print(results)

def run_test(tests: list[int]):
    all_test_results = []
    
    for test in tests:
        result = generate_and_measure(1, test)
        result_list = bitstrings_to_numbers(result)
        
        if not result_list:
            continue
            
        runs = []
        current_len = 1
        
        for i in range(1, len(result_list)):
            if result_list[i] == result_list[i - 1]:
                current_len += 1
            else:
                runs.append({'number': str(result_list[i - 1]), 'length': current_len})
                current_len = 1
        
        # Zapisujemy ostatnią serię po wyjściu z pętli
        runs.append({'number': str(result_list[-1]), 'length': current_len})
        all_test_results.append(runs)
        
    return all_test_results

def chi_square_test_for_quantum_rng(n_qubits: int, n_shots: int, alpha: float = 0.05):
    # 1. Przygotowanie i pomiar obwodu
    qc = generate_dynamic_circuit(n_qubits)
    qc.measure_all()
    
    res = get_results(qc, n_shots)
    counts = res[0].data.meas.get_counts()
    
    # 2. Mapowanie wyników na wszystkie możliwe stany (0 do 2^n - 1)
    num_states = 2**n_qubits
    observed_counts = []
    
    for i in range(num_states):
        # Formatowanie do ciągu bitów z dopisaniem zer wiodących
        bitstring = format(i, f'0{n_qubits}b')
        observed_counts.append(counts.get(bitstring, 0))
    
    # 3. Wartość oczekiwana dla każdego stanu
    expected_count = n_shots / num_states
    expected_counts = [expected_count] * num_states
    
    # 4. Obliczenie statystyki chi-kwadrat
    chi2_stat, p_value = stats.chisquare(f_obs=observed_counts, f_exp=expected_counts)
    
    degrees_of_freedom = num_states - 1
    critical_value = stats.chi2.ppf(1 - alpha, degrees_of_freedom)
    
    # 5. Wyświetlenie wyników
    print(f"--- TEST CHI-KWADRAT DLA {n_qubits} KUBITÓW (Shots: {n_shots}) ---")
    print(f"Liczba możliwych stanów (k): {num_states}")
    print(f"Oczekiwana zliczeń na stan: {expected_count}")
    print(f"Statystyka Chi-kwadrat (chi2_emp): {chi2_stat:.4f}")
    print(f"Wartość krytyczna (alpha={alpha}, df={degrees_of_freedom}): {critical_value:.4f}")
    print(f"p-value: {p_value:.4f}")
    
    if chi2_stat <= critical_value:
        print("\nWniosek: BRAK PODSTAW DO ODRZUCENIA H0.")
        print("Generator kwantowy generuje stany zgodnie z idealnym rozkładem jednostajnym.")
    else:
        print("\nWniosek: ODRZUCAMY H0.")
        print("Generator wykazuje istotne statystycznie odchylenie od rozkładu jednostajnego.")

# Uruchomienie dla 4 kubitów i 1000 strzałów
chi_square_test_for_quantum_rng(n_qubits=4, n_shots=1000)
    
statictical_distribution(4, [1000])
print(run_test([100]))