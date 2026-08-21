interface FilterBarProps {
  states: string[];
  cities: string[];
  selectedState: string;
  selectedCity: string;
  onStateChange: (state: string) => void;
  onCityChange: (city: string) => void;
}

const ALL = 'All';

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
          <option value={ALL}>All states</option>
          {states.map((state) => (
            <option key={state} value={state}>
              {state}
            </option>
          ))}
        </select>
      </label>

      <label className="filter-field">
        <span>City</span>
        <select value={selectedCity} onChange={(e) => onCityChange(e.target.value)}>
          <option value={ALL}>All cities</option>
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

export { ALL as ALL_OPTION };
