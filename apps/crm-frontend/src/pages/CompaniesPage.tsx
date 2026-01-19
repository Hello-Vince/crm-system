import { useQuery } from '@apollo/client';
import { GET_COMPANIES } from '../graphql/queries';
import { Company } from '../types/generated';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';

export function CompaniesPage() {
  const { data, loading, error, refetch } = useQuery<{ companies: Company[] }>(GET_COMPANIES);

  if (loading) return <LoadingSpinner message="Loading companies..." />;
  if (error) return <ErrorMessage error={error} />;

  const companies = data?.companies || [];

  // Separate root companies (no parent) and child companies
  const rootCompanies = companies.filter(c => !c.parent);
  const childCompanies = companies.filter(c => c.parent);

  const cardStyle = {
    backgroundColor: 'white',
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '16px',
  };

  const buttonStyle = {
    padding: '10px 20px',
    backgroundColor: '#3498db',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  };

  const companyItemStyle = {
    padding: '12px',
    borderBottom: '1px solid #eee',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Company Hierarchy</h1>
        <button style={buttonStyle} onClick={() => refetch()}>
          Refresh
        </button>
      </div>

      <p style={{ color: '#666', marginBottom: '24px' }}>
        This view demonstrates the parent/child company hierarchy from the Identity Service.
      </p>

      {companies.length === 0 ? (
        <p style={{ textAlign: 'center', color: '#666', padding: '40px' }}>
          No companies found. Please create companies via Django Admin.
        </p>
      ) : (
        <>
          <div style={cardStyle}>
            <h2 style={{ marginTop: 0, marginBottom: '16px', color: '#2c3e50' }}>
              Root Companies ({rootCompanies.length})
            </h2>
            {rootCompanies.length === 0 ? (
              <p style={{ color: '#666' }}>No root companies</p>
            ) : (
              rootCompanies.map(company => (
                <div key={company.id} style={companyItemStyle}>
                  <div>
                    <div style={{ fontWeight: 'bold', fontSize: '16px' }}>
                      {company.name}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                      ID: {company.id}
                    </div>
                  </div>
                  <div style={{ 
                    backgroundColor: '#3498db', 
                    color: 'white', 
                    padding: '4px 12px', 
                    borderRadius: '12px',
                    fontSize: '12px',
                  }}>
                    ROOT
                  </div>
                </div>
              ))
            )}
          </div>

          <div style={cardStyle}>
            <h2 style={{ marginTop: 0, marginBottom: '16px', color: '#2c3e50' }}>
              Child Companies ({childCompanies.length})
            </h2>
            {childCompanies.length === 0 ? (
              <p style={{ color: '#666' }}>No child companies</p>
            ) : (
              childCompanies.map(company => (
                <div key={company.id} style={companyItemStyle}>
                  <div>
                    <div style={{ fontWeight: 'bold', fontSize: '16px' }}>
                      {company.name}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                      ID: {company.id}
                    </div>
                    {company.parent && (
                      <div style={{ 
                        fontSize: '12px', 
                        color: '#3498db', 
                        marginTop: '4px',
                      }}>
                        ↳ Child of: {company.parent.name}
                      </div>
                    )}
                  </div>
                  <div style={{ 
                    backgroundColor: '#9b59b6', 
                    color: 'white', 
                    padding: '4px 12px', 
                    borderRadius: '12px',
                    fontSize: '12px',
                  }}>
                    CHILD
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
