import { useState, useEffect } from 'react';
import type { FC, FormEvent } from 'react';
import {
  MapPin,
  Search,
  Navigation,
  Phone,
  Clock,
  ExternalLink,
  AlertTriangle,
  Building2,
  RefreshCw
} from 'lucide-react';
import type { JanAushadhiKendra, KendraSearchResponse } from '../types';
import { searchKendras } from '../api';

export const KendraFinderView: FC = () => {
  const [query, setQuery] = useState<string>('');
  const [kendras, setKendras] = useState<JanAushadhiKendra[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [geoLoading, setGeoLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [userCoords, setUserCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [stockDisclaimer, setStockDisclaimer] = useState<string>('');
  const [searchNote, setSearchNote] = useState<string | null>(null);

  const executeSearch = async (searchQ?: string, lat?: number, lng?: number) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res: KendraSearchResponse = await searchKendras(searchQ, lat, lng, 12);
      setKendras(res.kendras);
      setStockDisclaimer(res.stock_verification_disclaimer);
      setSearchNote(res.search_note || null);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to search Jan Aushadhi Kendras.');
    } finally {
      setLoading(false);
    }
  };

  // Initial load: show network
  useEffect(() => {
    executeSearch();
  }, []);

  const handleSearchSubmit = (e: FormEvent) => {
    e.preventDefault();
    executeSearch(query.trim() || undefined, userCoords?.lat, userCoords?.lng);
  };

  const handleGeolocation = () => {
    if (!navigator.geolocation) {
      setErrorMsg('Browser geolocation is not supported on this device.');
      return;
    }
    setGeoLoading(true);
    setErrorMsg(null);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const coords = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude
        };
        setUserCoords(coords);
        setGeoLoading(false);
        // When user asks for GPS location, search nearest stores directly
        executeSearch(query.trim() || undefined, coords.lat, coords.lng);
      },
      () => {
        setGeoLoading(false);
        setErrorMsg('Location permission denied or unavailable. You can search by entering your city or 6-digit PIN code.');
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  const handleClearQuery = () => {
    setQuery('');
    executeSearch(undefined, userCoords?.lat, userCoords?.lng);
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0f766e', fontWeight: 700, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
          <Building2 className="w-4 h-4" />
          <span>PMBJP Verified Pharmacy Locator</span>
        </div>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
          Find Nearby Jan Aushadhi Kendras
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '720px' }}>
          Locate verified Pradhan Mantri Bhartiya Janaushadhi Kendras across Indian metropolitan and regional districts. Calculate accurate distance, view official contact details, and open GPS directions.
        </p>
      </div>

      {/* Non-Negotiable Stock Availability Disclaimer Box */}
      <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 'var(--radius-lg)', padding: '1rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
        <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" style={{ marginTop: '2px' }} />
        <div>
          <div style={{ fontWeight: 800, fontSize: '0.85rem', color: '#92400e', marginBottom: '0.2rem' }}>
            CRITICAL STOCK NOTICE: Inventory Not Verified Live
          </div>
          <div style={{ fontSize: '0.8rem', color: '#78350f', lineHeight: '1.4' }}>
            {stockDisclaimer || 'Stock availability has not been verified. MedLedger validates official Kendra registry locations, but individual store inventory fluctuates daily. Always call the Kendra by phone before traveling.'}
          </div>
        </div>
      </div>

      {/* Search & Location Bar */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', padding: '1.25rem', marginBottom: '1.75rem' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '240px', position: 'relative' }}>
            <Search className="w-4 h-4 text-slate-400" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search by city (e.g. 'Delhi', 'Bengaluru', 'Mumbai') or 6-digit PIN code (e.g. '110029')..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem 0.85rem 0.65rem 2.25rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-app)',
                color: 'var(--text-primary)',
                fontSize: '0.88rem'
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="search-button"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.65rem 1.1rem', fontSize: '0.85rem' }}
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            <span>Search Kendras</span>
          </button>

          <button
            type="button"
            onClick={handleGeolocation}
            disabled={geoLoading}
            style={{
              background: userCoords ? '#ecfdf5' : 'var(--bg-app)',
              border: `1px solid ${userCoords ? '#a7f3d0' : 'var(--border-subtle)'}`,
              borderRadius: 'var(--radius-md)',
              padding: '0.65rem 1rem',
              color: userCoords ? '#065f46' : 'var(--text-primary)',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem'
            }}
          >
            <Navigation className={`w-4 h-4 ${geoLoading ? 'animate-spin' : (userCoords ? 'text-teal-600' : 'text-slate-500')}`} />
            <span>{userCoords ? 'Location Active' : 'Use My GPS'}</span>
          </button>
        </form>

        {/* Quick Filter Chips */}
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.75rem', alignItems: 'center' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Quick Locations:</span>
          {['Lucknow (226010)', 'New Delhi (110029)', 'Bengaluru (560002)', 'Mumbai (400012)', 'Pune (411001)', 'Chennai (600003)', 'Hyderabad (500012)', 'Kolkata (700073)'].map((chip) => {
            const cityName = chip.split(' ')[0];
            return (
              <button
                key={chip}
                type="button"
                onClick={() => {
                  setQuery(cityName);
                  executeSearch(cityName, userCoords?.lat, userCoords?.lng);
                }}
                style={{
                  background: 'none',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-full)',
                  padding: '0.2rem 0.6rem',
                  fontSize: '0.72rem',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer'
                }}
              >
                {chip}
              </button>
            );
          })}
          {query && (
            <button
              type="button"
              onClick={handleClearQuery}
              style={{
                background: '#f1f5f9',
                border: '1px solid #cbd5e1',
                borderRadius: 'var(--radius-full)',
                padding: '0.2rem 0.6rem',
                fontSize: '0.72rem',
                color: '#475569',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              ✕ Clear Filter
            </button>
          )}
        </div>
      </div>

      {searchNote && (
        <div style={{ background: '#f0fdfa', border: '1px solid #99f6e4', borderRadius: 'var(--radius-md)', padding: '0.65rem 0.85rem', marginBottom: '1.25rem', color: '#0f766e', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <MapPin className="w-4 h-4 flex-shrink-0" />
          <span>{searchNote}</span>
        </div>
      )}

      {errorMsg && (
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 'var(--radius-md)', padding: '0.75rem', marginBottom: '1.5rem', color: '#991b1b', fontSize: '0.85rem' }}>
          {errorMsg}
        </div>
      )}

      {/* Results Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(310px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {kendras.map((kendra) => (
          <div
            key={kendra.kendra_id}
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-xl)',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between'
            }}
          >
            <div>
              {/* Header: ID + Distance */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#0f766e', background: '#f0fdfa', padding: '0.15rem 0.45rem', borderRadius: 'var(--radius-sm)' }}>
                  {kendra.kendra_id}
                </span>
                {kendra.distance_km !== null && kendra.distance_km !== undefined && (
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#059669', background: '#ecfdf5', padding: '0.15rem 0.5rem', borderRadius: 'var(--radius-full)' }}>
                    📍 {kendra.distance_km} km away
                  </span>
                )}
              </div>

              {/* Title & Address */}
              <h4 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                {kendra.kendra_name}
              </h4>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '0.75rem', lineHeight: '1.35' }}>
                {kendra.address}, {kendra.city_or_district}, {kendra.state} - <b>{kendra.pincode}</b>
              </p>

              {/* Contact & Hours */}
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.25rem', marginBottom: '1rem' }}>
                {kendra.contact_number && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <Phone className="w-3.5 h-3.5 text-teal-600" />
                    <span><b>Phone:</b> {kendra.contact_number}</span>
                  </div>
                )}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  <span><b>Hours:</b> {kendra.operating_hours}</span>
                </div>
              </div>
            </div>

            {/* Directions Action */}
            {kendra.directions_url && (
              <a
                href={kendra.directions_url}
                target="_blank"
                rel="noopener noreferrer"
                className="verify-link-button"
                style={{ width: '100%', justifyContent: 'center', textDecoration: 'none' }}
              >
                <MapPin className="w-4 h-4" />
                <span>Get Directions (Google Maps)</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>
        ))}
      </div>

      {kendras.length === 0 && !loading && (
        <div style={{ textAlign: 'center', padding: '3rem 1rem', background: 'var(--bg-card)', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
          <MapPin className="w-10 h-10 text-slate-300" style={{ margin: '0 auto 0.75rem auto' }} />
          <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
            No Kendra found for this location
          </div>
          <div style={{ fontSize: '0.85rem' }}>
            Try searching for a larger neighboring city or state name (e.g. Delhi, Bengaluru, Mumbai).
          </div>
        </div>
      )}
    </div>
  );
};
