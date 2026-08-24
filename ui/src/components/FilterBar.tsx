interface FilterBarProps {
  states: string[];
  cities: string[];
  selectedState: string;
  selectedCity: string;
  onStateChange: (state: string) => void;
  onCityChange: (city: string) => void;
}

export function FilterBar({
  states,
  cities,
  selectedState,
  selectedCity,
  onStateChange,
  onCityChange,
}: FilterBarProps) {
  return (
    <div className="filter-bar">
      <label className="filter-field">
        <span>State</span>
        <select value={selectedState} onChange={(e) => onStateChange(e.target.value)}>
          <option value="">Select a state</option>
          {states.map((state) => (
            <option key={state} value={state}>
              {state}
            </option>
          ))}
        </select>
      </label>

      <label className="filter-field">
        <span>City</span>
        <select
          value={selectedCity}
          onChange={(e) => onCityChange(e.target.value)}
          disabled={!selectedState}
        >
          <option value="">Select a city</option>
          {cities.map((city) => (
            <option key={city} value={city}>
              {city}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
