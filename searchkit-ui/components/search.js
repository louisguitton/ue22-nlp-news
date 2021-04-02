import { useSearchkitQuery } from "@searchkit/client";
import { gql } from "@apollo/client";

import {
    FacetsList,
    SearchBar,
    Pagination,
    ResetSearchButton,
    SelectedFilters,
} from "@searchkit/elastic-ui";

import {
    EuiPage,
    EuiPageBody,
    EuiPageContent,
    EuiPageContentBody,
    EuiPageContentHeader,
    EuiPageContentHeaderSection,
    EuiPageHeader,
    EuiPageHeaderSection,
    EuiPageSideBar,
    EuiTitle,
    EuiHorizontalRule,
    EuiBadge,
    EuiFlexGroup,
    EuiFlexGrid,
    EuiFlexItem,
    EuiCard,
    EuiText,
} from "@elastic/eui";

const query = gql`
  query resultSet(
    $query: String
    $filters: [SKFiltersSet]
    $page: SKPageInput
    $sortBy: String
  ) {
    results(query: $query, filters: $filters) {
      summary {
        total
        appliedFilters {
          id
          identifier
          display
          label
          ... on DateRangeSelectedFilter {
            dateMin
            dateMax
          }

          ... on NumericRangeSelectedFilter {
            min
            max
          }

          ... on ValueSelectedFilter {
            value
          }
        }
        sortOptions {
          id
          label
        }
        query
      }
      hits(page: $page, sortBy: $sortBy) {
        page {
          total
          totalPages
          pageNumber
          from
          size
        }
        sortedBy
        items {
          ... on ResultHit {
            id
            fields {
              title
              description
              content
              source_name
              author
              url
              published_at
              url_to_image
            }
          }
        }
      }
      facets {
        identifier
        type
        label
        display
        entries {
          id
          label
          count
        }
      }
    }
  }
`;

export const HitsList = ({ data }) => (
    <>
        <EuiFlexGrid columns={2} gutterSize="m">
            {data?.results.hits.items.map((hit) => (
                <EuiFlexItem>
                    <EuiCard
                        grow={false}
                        textAlign="left"
                        title={hit.fields.title}
                        description={hit.fields.description}
                        image={
                            <img
                                src={hit.fields.url_to_image}
                                style={{ maxWidth: 200 }}
                                alt="Article Image"
                            />
                        }
                        onClick={() => {
                            window.open(hit.fields.url, "_blank");
                        }}>
                        <EuiText size="s">
                            <EuiBadge color="primary">{hit.fields.source_name}</EuiBadge>
                            <EuiBadge color="secondary">
                                {hit.fields.published_at}
                            </EuiBadge>
                        </EuiText>
                    </EuiCard>
                </EuiFlexItem>
            ))}
        </EuiFlexGrid>
    </>
);

export default () => {
    const { data, loading } = useSearchkitQuery(query);
    const Facets = FacetsList([]);
    return (
        <EuiPage>
            <EuiPageSideBar>
                <SearchBar loading={loading} />
                <EuiHorizontalRule margin="m" />
                <Facets data={data?.results} loading={loading} />
            </EuiPageSideBar>
            <EuiPageBody component="div">
                <EuiPageHeader>
                    <EuiPageHeaderSection>
                        <EuiTitle size="l">
                            <SelectedFilters data={data?.results} loading={loading} />
                        </EuiTitle>
                    </EuiPageHeaderSection>
                    <EuiPageHeaderSection>
                        <ResetSearchButton loading={loading} />
                    </EuiPageHeaderSection>
                </EuiPageHeader>
                <EuiPageContent>
                    <EuiPageContentHeader>
                        <EuiPageContentHeaderSection>
                            <EuiTitle size="s">
                                <h2>{data?.results.summary.total} Results</h2>
                            </EuiTitle>
                        </EuiPageContentHeaderSection>
                    </EuiPageContentHeader>
                    <EuiPageContentBody>
                        <HitsList data={data} />
                        <EuiFlexGroup justifyContent="spaceAround">
                            <Pagination data={data?.results} />
                        </EuiFlexGroup>
                    </EuiPageContentBody>
                </EuiPageContent>
            </EuiPageBody>
        </EuiPage>
    );
};
