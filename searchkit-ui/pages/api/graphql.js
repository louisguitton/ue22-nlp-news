// https://www.searchkit.co/docs/quick-start/api-setup
import { ApolloServer, gql } from 'apollo-server-micro'
import {
    MultiMatchQuery,
    RefinementSelectFacet,
    DateRangeFacet,
    SearchkitSchema
} from '@searchkit/schema'
import { GraphQLScalarType } from 'graphql';
import { Kind } from 'graphql/language';

const searchkitConfig = {
    host: process.env.ES_HOST || 'http://localhost:9200',
    index: 'articles',
    hits: {
        fields: [
            'id', 
            'title', 
            'description', 
            'content', 
            'source_name', 
            'author', 
            'url', 
            'published_at',
            'urlToImage'
        ]
    },
    // boost importance of title by 4
    query: new MultiMatchQuery({ fields: ['title^4', 'description', 'content'] }),
    facets: [
        // TODO: check that facets are working
        new RefinementSelectFacet({
            field: 'source_name',
            identifier: 'source',
            label: 'Source',
            multipleSelect: true
        }),
        new DateRangeFacet({
            field: 'published_at',
            identifier: 'published_at',
            label: 'Published'
        }),

    ]
}

// Returns SDL + Resolvers for searchkit, based on the Searchkit config
const { typeDefs, withSearchkitResolvers, context } = SearchkitSchema({
    config: searchkitConfig, // searchkit configuration
    typeName: 'ResultSet', // type name for Searchkit Root
    hitTypeName: 'ResultHit', // type name for each search result
    addToQueryType: true // When true, adds a field called results to Query type 
})

export const config = {
    api: {
        bodyParser: false
    }
}

const server = new ApolloServer({
    // Type name should match the hit typename
    typeDefs: [
        gql`
    scalar Date

    type Query {
      root: String
    }

    type HitFields {
        title: String
        description: String
        content: String
        source_name: String
        author: String
        url: String
        published_at: Date
        urlToImage: String
    }

    type ResultHit implements SKHit {
      id: ID!
      fields: HitFields
    }
  `, ...typeDefs
    ],
    resolvers: withSearchkitResolvers({
        // https://stackoverflow.com/questions/49693928/date-and-json-in-type-definition-for-graphql
        Date: new GraphQLScalarType({
            name: 'Date',
            description: 'Date custom scalar type',
            parseValue(value) {
                return new Date(value); // value sent to the client
                // return value.getTime(); // value from the client
            },
            serialize(value) {
                return new Date(value).toDateString(); // value sent to the client
            },
            parseLiteral(ast) {
                if (ast.kind === Kind.INT) {
                    return parseInt(ast.value, 10); // ast value is always in string format
                }
                return null;
            },
        })
    }),
    introspection: true,
    playground: true,
    context: {
        ...context
    }
})

const handler = server.createHandler({ path: '/api/graphql' })

export default handler
